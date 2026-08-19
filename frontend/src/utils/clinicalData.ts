export interface EncounterInfo {
  specialty: string
  label: string
  triage: 'emergency' | 'urgent' | 'routine'
  redFlags: string[]
  questions: string[]
}

const EMERGENCY_SPECIALTIES = new Set(['emergency'])

const ENCOUNTER_MAP: Record<string, EncounterInfo> = {
  emergency: {
    specialty: 'emergency',
    label: 'Emergency / Trauma',
    triage: 'emergency',
    redFlags: [
      'Chest pain or pressure',
      'Difficulty breathing',
      'Sudden weakness or numbness on one side',
      'Sudden severe headache',
      'Uncontrolled bleeding',
      'Loss of consciousness',
    ],
    questions: [
      'Is this a life-threatening emergency? Call 112 / 108 / 911 now.',
      'What is the estimated time to the nearest ER?',
      'Do I need an ambulance or can I be driven?',
    ],
  },
  cardiology: {
    specialty: 'cardiology',
    label: 'Cardiology',
    triage: 'urgent',
    redFlags: ['Chest pain', 'Shortness of breath', 'Racing or irregular heartbeat', 'Dizziness or fainting'],
    questions: [
      'What heart tests (ECG, echo, stress test) do I need?',
      'Are my current symptoms signs of an acute event?',
      'Should I adjust my blood pressure or cholesterol medication?',
    ],
  },
  orthopedics: {
    specialty: 'orthopedics',
    label: 'Orthopedics',
    triage: 'urgent',
    redFlags: ['Deformity or inability to bear weight', 'Severe swelling', 'Numbness or tingling below the injury'],
    questions: [
      'Do I need an X-ray or MRI?',
      'Is surgery required or is conservative treatment enough?',
      'What activity restrictions and physiotherapy do I need?',
    ],
  },
  neurology: {
    specialty: 'neurology',
    label: 'Neurology',
    triage: 'urgent',
    redFlags: ['Sudden confusion', 'Sudden severe headache', 'Facial drooping', 'Loss of consciousness', 'New weakness'],
    questions: [
      'Do I need brain imaging (CT/MRI)?',
      'Could these symptoms indicate a stroke?',
      'What follow-up or specialist referral do I need?',
    ],
  },
  oncology: {
    specialty: 'oncology',
    label: 'Oncology',
    triage: 'urgent',
    redFlags: ['Unexplained weight loss', 'New lumps or growths', 'Persistent bleeding', 'Severe fatigue'],
    questions: [
      'What diagnostic tests and staging are needed?',
      'What treatment options are available?',
      'Should I seek a second opinion?',
    ],
  },
  psychiatry: {
    specialty: 'psychiatry',
    label: 'Psychiatry / Mental Health',
    triage: 'urgent',
    redFlags: ['Thoughts of self-harm', 'Severe agitation or panic', 'Inability to care for oneself'],
    questions: [
      'What therapy or medication options suit my situation?',
      'Are there crisis support numbers I should have?',
      'How soon should I schedule a follow-up?',
    ],
  },
  general: {
    specialty: 'general',
    label: 'Primary Care / General Medicine',
    triage: 'routine',
    redFlags: ['High fever', 'Severe pain', 'Shortness of breath', 'Persistent vomiting'],
    questions: [
      'What is the likely cause of my symptoms?',
      'Which tests should I take?',
      'When should I return for a follow-up?',
    ],
  },
}

const DEFAULT_ENCOUNTER: EncounterInfo = {
  specialty: 'general',
  label: 'General Care',
  triage: 'routine',
  redFlags: ['High fever', 'Severe pain', 'Shortness of breath', 'Persistent vomiting'],
  questions: [
    'What is the likely cause of my symptoms?',
    'Which tests should I take?',
    'When should I return for a follow-up?',
  ],
}

export function getEncounterInfo(specialty: string): EncounterInfo {
  return ENCOUNTER_MAP[specialty] ?? (EMERGENCY_SPECIALTIES.has(specialty) ? ENCOUNTER_MAP.emergency : DEFAULT_ENCOUNTER)
}