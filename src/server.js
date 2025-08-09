import 'dotenv/config';
import express from 'express';
import helmet from 'helmet';
import morgan from 'morgan';
import bodyParser from 'body-parser';
import Joi from 'joi';
import { v4 as uuidv4 } from 'uuid';
import twilio from 'twilio';

const app = express();
app.use(helmet());
app.use(morgan('dev'));
app.use(bodyParser.urlencoded({ extended: false }));
app.use(bodyParser.json());

const {
  PORT = 3000,
  PUBLIC_BASE_URL,
  TWILIO_ACCOUNT_SID,
  TWILIO_AUTH_TOKEN,
  TWILIO_CALLER_NUMBER,
  TWILIO_LANGUAGE = 'sl-SI',
  TWILIO_VOICE = 'Polly.Joanna',
  WEBHOOK_AUTH_TOKEN,
  ASR_HINTS = ''
} = process.env;

if (!PUBLIC_BASE_URL) {
  console.warn('PUBLIC_BASE_URL is not set. Webhooks will not be reachable by Twilio.');
}

const twilioClient = twilio(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN);

const memoryStore = new Map();

function validateAuth(req, res, next) {
  const token = req.query.token || req.headers['x-webhook-token'];
  if (!WEBHOOK_AUTH_TOKEN) return next();
  if (token !== WEBHOOK_AUTH_TOKEN) return res.status(401).send('Unauthorized');
  return next();
}

const initiateCallSchema = Joi.object({
  companyName: Joi.string().min(2).max(200).required(),
  phoneNumber: Joi.string().pattern(/^[+0-9][0-9\- ()]{6,}$/).required()
});

app.post('/api/call', async (req, res) => {
  const { error, value } = initiateCallSchema.validate(req.body);
  if (error) return res.status(400).json({ error: error.details[0].message });

  const { companyName, phoneNumber } = value;
  const callId = uuidv4();

  memoryStore.set(callId, {
    companyName,
    stage: 'intro',
    attempts: 0,
    objections: [],
    createdAt: Date.now()
  });

  try {
    const twimlUrl = `${PUBLIC_BASE_URL}/voice/answer?callId=${encodeURIComponent(callId)}&token=${encodeURIComponent(WEBHOOK_AUTH_TOKEN || '')}`;
    const call = await twilioClient.calls.create({
      to: phoneNumber,
      from: TWILIO_CALLER_NUMBER,
      url: twimlUrl,
      machineDetection: 'Enable',
      machineDetectionTimeout: 6
    });
    return res.json({ callId, sid: call.sid, status: call.status });
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: 'Failed to create call', details: err.message });
  }
});

function say(text) {
  const voice = TWILIO_VOICE;
  return `<Say language="${TWILIO_LANGUAGE}" voice="${voice}">${escapeXml(text)}</Say>`;
}

function listen(gatherOpts = {}) {
  const hints = ASR_HINTS;
  const input = gatherOpts.input || 'speech';
  const timeout = gatherOpts.timeout ?? 6;
  const speechTimeout = gatherOpts.speechTimeout || 'auto';
  const action = gatherOpts.action;
  const method = 'POST';
  const hintsAttr = hints ? ` speechModel="phone_call" hints="${escapeXml(hints)}"` : ' speechModel="phone_call"';
  return `<Gather input="${input}" timeout="${timeout}" speechTimeout="${speechTimeout}" action="${action}" method="${method}"${hintsAttr}>${gatherOpts.children || ''}</Gather>`;
}

function hangup() {
  return '<Hangup />';
}

function redirect(url) {
  return `<Redirect method="POST">${escapeXml(url)}</Redirect>`;
}

function response(children) {
  return `<?xml version="1.0" encoding="UTF-8"?><Response>${children}</Response>`;
}

function escapeXml(unsafe) {
  return String(unsafe)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function nextStage(state, transcript) {
  const lower = (transcript || '').toLowerCase();
  if (state.stage === 'intro') {
    state.stage = 'qualify';
    return say(`Dober dan! Govorim z ${state.companyName}? Jaz sem virtualni asistent. Hitro vprašanje: ali ste zadovoljni z vašo trenutno spletno stranjo in koliko vam prinaša novih strank?`) + listen({ action: `${PUBLIC_BASE_URL}/voice/qualify?callId=${state.idParam}` });
  }
  if (state.stage === 'qualify') {
    if (/nimamo|nimam|ni|brez.*spletne|nimamo spletne/i.test(lower)) {
      state.stage = 'pitch_no_site';
      return say('Razumem. Prav zato vam lahko v nekaj dneh pripravimo preprosto, moderno spletno stran, ki vas predstavi in prinese povpraševanja. Če vam v 30 dneh ne prinese potencialnih strank, ne zaračunamo. Vas zanima kratka predstavitev?') + listen({ action: `${PUBLIC_BASE_URL}/voice/handle?callId=${state.idParam}` });
    }
    state.stage = 'pitch_upgrade';
    return say('Super. Veliko podjetij ima spletno stran, ki pa ne prinaša dovolj povpraševanj. Mi izboljšamo vsebino, hitrost in vidnost v iskalnikih. Običajno to prinese 20–50% več klicev v 2–3 mesecih. Bi vam ustrezal kratek 10-min pogovor, da preverimo priložnosti?') + listen({ action: `${PUBLIC_BASE_URL}/voice/handle?callId=${state.idParam}` });
  }
  if (state.stage.startsWith('pitch')) {
    // Objection handling
    const objection = detectObjection(lower);
    if (objection) state.objections.push(objection);
    const reply = handleObjection(objection);
    state.attempts += 1;
    if (/da|lahko|ok|uredu|dogovorjeno|super|zanimivo/.test(lower)) {
      state.stage = 'schedule';
      return say('Odlično! Predlagam, da uskladimo kratek termin. Kdaj vam bolj ustreza: jutri dopoldne ali v sredo po 14. uri?') + listen({ action: `${PUBLIC_BASE_URL}/voice/schedule?callId=${state.idParam}` });
    }
    if (/ne|nikoli|ne zanima|pusti|hvala/.test(lower) && state.attempts >= 2) {
      state.stage = 'wrap';
      return say('Popolnoma razumem. Hvala za vaš čas. Če boste kdaj želeli brezplačen pregled spletne prisotnosti, smo na voljo. Lep dan!') + hangup();
    }
    if (state.attempts >= 3) {
      state.stage = 'wrap';
      return say('Da ne zadržujem, poslali bomo kratek povzetek na e-pošto, če želite. Hvala za pogovor in lep dan!') + hangup();
    }
    return say(reply) + listen({ action: `${PUBLIC_BASE_URL}/voice/handle?callId=${state.idParam}` });
  }
  if (state.stage === 'schedule') {
    if (/jutri|torek|sreda|četrtek|petek|dopoldne|popoldne|14|15|16/.test(lower)) {
      state.stage = 'wrap';
      return say('Zapisal sem. Poslal bom koledarski termin in kratek povzetek. Hvala in lep dan!') + hangup();
    }
    return say('Razumem. Izberite vam primeren dan in uro, na primer jutri dopoldne ali sredo po 14. uri.') + listen({ action: `${PUBLIC_BASE_URL}/voice/schedule?callId=${state.idParam}` });
  }
  state.stage = 'wrap';
  return say('Hvala za vaš čas. Lep dan!') + hangup();
}

function detectObjection(text) {
  if (!text) return null;
  if (/nimam časa|zaseden|trenutno ne/.test(text)) return 'time';
  if (/pre(drago|visoko)|cena|proračun/.test(text)) return 'price';
  if (/že imamo|že delamo|partner|agencij/.test(text)) return 'have_vendor';
  if (/pošljite.*mail|e-?pošto|email/.test(text)) return 'send_email';
  if (/ne zanima|ne potrebujem|ni prioriteta/.test(text)) return 'not_interested';
  if (/pokličite kasneje|kasneje/.test(text)) return 'call_later';
  return 'generic';
}

function handleObjection(kind) {
  switch (kind) {
    case 'time':
      return 'Popolnoma razumem. Potrebujemo le 30 sekund, da povem bistvo, in če ne vidite vrednosti, zaključimo. Se strinjate?';
    case 'price':
      return 'Razumem skrb glede cene. Za mala podjetja imamo začetni paket in plačilo vezano na rezultate. Najprej preverimo potencial, nato govorimo o številkah. Je to pošteno?';
    case 'have_vendor':
      return 'Odlično, da imate partnerja. Veliko strank nas uporabi kot drugi par oči za ideje, ki jih vaš partner lahko izvede. Lahko v 10 minutah delimo 2–3 konkretne priložnosti?';
    case 'send_email':
      return 'Z veseljem pošljem povzetek. Da ne ostane pri emailu, predlagam kratek klic, kjer se osredotočimo na 1–2 področji z največjim učinkom. Kdaj bi vam ustrezalo?';
    case 'not_interested':
      return 'Razumem. Običajno se izkaže, da drobne izboljšave prinesejo merljiv učinek brez velikih vložkov. Če v 30 dneh ne vidite koristi, ne zaračunamo. Damo priložnost za hiter pregled?';
    case 'call_later':
      return 'Ni težava. Lahko uskladimo konkreten termin, da bomo učinkoviti – jutri dopoldne ali sreda po 14. uri?';
    default:
      return 'Razumem. Predlagam kratek, konkreten pregled vašega primera in možnosti za več povpraševanj. Bi to bilo smiselno?';
  }
}

function getState(callId) {
  const s = memoryStore.get(callId);
  if (!s) return null;
  return { ...s, idParam: `${encodeURIComponent(callId)}&token=${encodeURIComponent(WEBHOOK_AUTH_TOKEN || '')}` };
}

app.post('/voice/answer', validateAuth, (req, res) => {
  const { callId } = req.query;
  const state = getState(callId);
  if (!state) return res.type('text/xml').send(response(say('Pri aparatu. Ali govorim z odgovorno osebo za vašo spletno prisotnost?') + listen({ action: `${PUBLIC_BASE_URL}/voice/qualify?callId=${encodeURIComponent(callId)}&token=${encodeURIComponent(WEBHOOK_AUTH_TOKEN || '')}` })));
  state.stage = 'intro';
  memoryStore.set(callId, state);
  const xml = response(
    say(`Dober dan pri telefonu. Kličem v podjetje ${state.companyName}. Ali govorim z odgovorno osebo za spletno stran?`) +
      listen({ action: `${PUBLIC_BASE_URL}/voice/qualify?callId=${state.idParam}` })
  );
  res.type('text/xml').send(xml);
});

app.post('/voice/qualify', validateAuth, (req, res) => {
  const { callId } = req.query;
  const transcript = req.body.SpeechResult || '';
  const state = getState(callId) || { companyName: 'podjetje', stage: 'intro', attempts: 0, objections: [], idParam: callId };
  const xmlChildren = nextStage(state, transcript);
  memoryStore.set(callId, state);
  res.type('text/xml').send(response(xmlChildren));
});

app.post('/voice/handle', validateAuth, (req, res) => {
  const { callId } = req.query;
  const transcript = req.body.SpeechResult || '';
  const state = getState(callId) || { companyName: 'podjetje', stage: 'pitch_upgrade', attempts: 0, objections: [], idParam: callId };
  const xmlChildren = nextStage(state, transcript);
  memoryStore.set(callId, state);
  res.type('text/xml').send(response(xmlChildren));
});

app.post('/voice/schedule', validateAuth, (req, res) => {
  const { callId } = req.query;
  const transcript = req.body.SpeechResult || '';
  const state = getState(callId) || { companyName: 'podjetje', stage: 'schedule', attempts: 0, objections: [], idParam: callId };
  const xmlChildren = nextStage(state, transcript);
  memoryStore.set(callId, state);
  res.type('text/xml').send(response(xmlChildren));
});

app.get('/health', (req, res) => res.json({ ok: true }));

app.listen(PORT, () => {
  console.log(`Voice server listening on :${PORT}`);
});