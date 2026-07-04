// persona.js -- Life-thread generator: one person per run, shown as quiet
// annotations under the world events. The birth year varies per seed: it is
// chosen so the persona is at a formative age when the run's hinge event —
// its most improbable high-impact divergence — arrives. Milestone variants
// are chosen by the run's world state at each life stage. Deterministic per
// seed; pure templates, no network calls.

// Locales, roughly population-weighted, each with culturally matched names.
// city = short prose form; place = birth-line form. surF overrides surnames
// for women where the language genders them (Russian, etc.).
const LOCALES = [
  { w: 17, city: 'Chengdu', place: 'Chengdu, China',
    f: ['Jing', 'Fang', 'Xiuying', 'Na'], m: ['Wei', 'Jun', 'Hao', 'Ming'],
    sur: ['Zhang', 'Wang', 'Li', 'Chen', 'Liu'] },
  { w: 18, city: 'Jaipur', place: 'Jaipur, India',
    f: ['Priya', 'Ananya', 'Divya', 'Kavya'], m: ['Arjun', 'Rahul', 'Vikram', 'Aditya'],
    sur: ['Sharma', 'Patel', 'Reddy', 'Singh', 'Iyer'] },
  { w: 4, city: 'Columbus', place: 'Columbus, Ohio',
    f: ['Emily', 'Madison', 'Ava'], m: ['Jacob', 'Tyler', 'Ethan'],
    sur: ['Miller', 'Johnson', 'Davis', 'Martinez'] },
  { w: 3.5, city: 'Surabaya', place: 'Surabaya, Indonesia',
    f: ['Dewi', 'Siti', 'Putri'], m: ['Budi', 'Agus', 'Eko'],
    sur: ['Santoso', 'Wijaya', 'Saputra'] },
  { w: 3, city: 'Lahore', place: 'Lahore, Pakistan',
    f: ['Ayesha', 'Fatima', 'Zainab'], m: ['Ali', 'Hassan', 'Bilal'],
    sur: ['Khan', 'Ahmed', 'Malik'] },
  { w: 3.5, city: 'Lagos', place: 'Lagos, Nigeria',
    f: ['Chiamaka', 'Amina', 'Folake'], m: ['Chinedu', 'Emeka', 'Ibrahim'],
    sur: ['Okafor', 'Adeyemi', 'Bello', 'Eze'] },
  { w: 3, city: 'Recife', place: 'Recife, Brazil',
    f: ['Ana', 'Juliana', 'Camila'], m: ['Lucas', 'Gabriel', 'Rafael'],
    sur: ['Silva', 'Santos', 'Oliveira', 'Ferreira'] },
  { w: 2.5, city: 'Dhaka', place: 'Dhaka, Bangladesh',
    f: ['Nusrat', 'Taslima', 'Farhana'], m: ['Rakib', 'Tanvir', 'Imran'],
    sur: ['Rahman', 'Hossain', 'Islam'] },
  { w: 2, city: 'Kazan', place: 'Kazan, Russia',
    f: ['Anastasia', 'Olga', 'Daria'], m: ['Dmitri', 'Sergei', 'Ivan'],
    sur: ['Ivanov', 'Petrov', 'Smirnov'], surF: ['Ivanova', 'Petrova', 'Smirnova'] },
  { w: 2, city: 'Guadalajara', place: 'Guadalajara, Mexico',
    f: ['Sofía', 'Valentina', 'Ximena'], m: ['Diego', 'Santiago', 'Alejandro'],
    sur: ['Hernández', 'García', 'Reyes'] },
  { w: 1.8, city: 'Osaka', place: 'Osaka, Japan',
    f: ['Yui', 'Sakura', 'Hana'], m: ['Haruto', 'Ren', 'Daiki'],
    sur: ['Tanaka', 'Sato', 'Yamamoto'] },
  { w: 2, city: 'Addis Ababa', place: 'Addis Ababa, Ethiopia',
    f: ['Selam', 'Hiwot', 'Meron'], m: ['Dawit', 'Bereket', 'Yonas'],
    sur: ['Tesfaye', 'Abebe', 'Girma'] },
  { w: 2, city: 'Cebu City', place: 'Cebu City, Philippines',
    f: ['Maria', 'Angelica', 'Jasmine'], m: ['Jose', 'Marco', 'Paolo'],
    sur: ['Santos', 'Reyes', 'dela Cruz'] },
  { w: 2, city: 'Alexandria', place: 'Alexandria, Egypt',
    f: ['Mariam', 'Nour', 'Salma'], m: ['Omar', 'Ahmed', 'Youssef'],
    sur: ['Hassan', 'Ibrahim', 'Mahmoud'] },
  { w: 1.8, city: 'Da Nang', place: 'Da Nang, Vietnam',
    f: ['Linh', 'Mai', 'Huong'], m: ['Minh', 'Duc', 'Quan'],
    sur: ['Nguyen', 'Tran', 'Le'] },
  { w: 1.5, city: 'Izmir', place: 'Izmir, Turkey',
    f: ['Zeynep', 'Elif', 'Merve'], m: ['Mehmet', 'Emre', 'Can'],
    sur: ['Yılmaz', 'Demir', 'Kaya'] },
  { w: 1.5, city: 'Isfahan', place: 'Isfahan, Iran',
    f: ['Zahra', 'Niloufar', 'Sara'], m: ['Reza', 'Amir', 'Hossein'],
    sur: ['Hosseini', 'Ahmadi', 'Karimi'] },
  { w: 1.2, city: 'Leipzig', place: 'Leipzig, Germany',
    f: ['Lena', 'Mia', 'Hannah'], m: ['Finn', 'Jonas', 'Lukas'],
    sur: ['Müller', 'Schmidt', 'Weber'] },
  { w: 1.2, city: 'Manchester', place: 'Manchester, England',
    f: ['Olivia', 'Amelia', 'Grace'], m: ['Oliver', 'Harry', 'Callum'],
    sur: ['Taylor', 'Walker', 'Hughes'] },
  { w: 1.2, city: 'Marseille', place: 'Marseille, France',
    f: ['Léa', 'Chloé', 'Manon'], m: ['Hugo', 'Louis', 'Théo'],
    sur: ['Martin', 'Bernard', 'Dubois'] },
  { w: 1.5, city: 'Nairobi', place: 'Nairobi, Kenya',
    f: ['Wanjiru', 'Achieng', 'Njeri'], m: ['Kamau', 'Otieno', 'Kiprop'],
    sur: ['Mwangi', 'Odhiambo', 'Njoroge'] },
  { w: 1, city: 'Busan', place: 'Busan, South Korea',
    f: ['Ji-woo', 'Seo-yeon', 'Ha-eun'], m: ['Min-jun', 'Ji-ho', 'Do-yun'],
    sur: ['Kim', 'Lee', 'Park'] },
  { w: 1, city: 'Medellín', place: 'Medellín, Colombia',
    f: ['Isabella', 'Mariana', 'Camila'], m: ['Juan', 'Andrés', 'Sebastián'],
    sur: ['Rodríguez', 'Gómez', 'López'] },
  { w: 1.5, city: 'Kinshasa', place: 'Kinshasa, DR Congo',
    f: ['Esperance', 'Grace', 'Chantal'], m: ['Emmanuel', 'Patrice', 'Dieudonné'],
    sur: ['Ilunga', 'Mbuyi', 'Kalala'] },
];
const TOTAL_WEIGHT = LOCALES.reduce((t, l) => t + l.w, 0);

function pickIdentity(rng) {
  let roll = rng() * TOTAL_WEIGHT;
  let locale = LOCALES[LOCALES.length - 1];
  for (const l of LOCALES) {
    roll -= l.w;
    if (roll <= 0) { locale = l; break; }
  }
  const female = rng() < 0.5;
  const givens = female ? locale.f : locale.m;
  const surs = (female && locale.surF) ? locale.surF : locale.sur;
  const given = givens[Math.floor(rng() * givens.length)];
  const sur = surs[Math.floor(rng() * surs.length)];
  return {
    name: `${given} ${sur}`,
    first: given,
    pron: female ? 'she' : 'he',
    poss: female ? 'her' : 'his',
    city: locale.city,
    place: locale.place,
  };
}

// Matches Viewer.INITIAL_STATE for the dimensions the life thread reads
const BASELINE = {
  us_polarization: 0.35, global_gdp_growth_modifier: 1.0,
  social_media_penetration: 0.05, misinformation_severity: 0.15,
  internet_freedom_index: 0.80, conflict_deaths: 0,
  automation_displacement: 0.0, ai_development_year_offset: 0,
  climate_temp_anomaly: 0.6, sea_level_rise_meters: 0.0,
  food_security_index: 0.85, global_democracy_index: 0.62,
  inequality_index: 0.50, us_life_expectancy_delta: 0.0,
  renewable_energy_share: 0.06,
};

// Deterministic PRNG (mulberry32) so the same seed always yields the same life
function mulberry32(seed) {
  let a = seed >>> 0;
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function stateTimeline(events) {
  const state = { ...BASELINE };
  const out = [];
  for (const e of events) {
    for (const [dim, delta] of Object.entries(e.world_state_delta || {})) {
      if (typeof delta === 'number' && dim in state) state[dim] += delta;
    }
    out.push([parseInt(e.year_month.slice(0, 4), 10), { ...state }]);
  }
  return out;
}

function stateAt(timeline, year) {
  let last = BASELINE;
  for (const [y, s] of timeline) {
    if (y > year) break;
    last = s;
  }
  return last;
}

// The run's hinge: its most improbable high-impact divergence
function findHinge(events) {
  let hinge = null, hingeIdx = -1;
  for (let i = 0; i < events.length; i++) {
    const e = events[i];
    if (!e.is_high_impact || e.status === 'HISTORICAL') continue;
    const p = e.probability_of_branch ?? 1;
    if (!hinge || p < (hinge.probability_of_branch ?? 1)) { hinge = e; hingeIdx = i; }
  }
  return { hinge, hingeIdx };
}

export function buildPersona(run) {
  const seed = run.seed;
  const rng = mulberry32(seed);
  const { name, first, pron, poss, city, place } = pickIdentity(rng);
  const events = run.events || [];
  if (events.length === 0) return null;
  const tl = stateTimeline(events);
  const endYear = parseInt(events[events.length - 1].year_month.slice(0, 4), 10);
  const cutShort = endYear < 2098;
  const cap = poss.charAt(0).toUpperCase() + poss.slice(1);

  // Birth year: put the persona at a formative age when the hinge arrives
  const { hinge, hingeIdx } = findHinge(events);
  const hingeYear = hinge ? parseInt(hinge.year_month.slice(0, 4), 10) : 2050;
  const vantages = [4, 9, 17, 26, 38, 61];
  const vantage = vantages[Math.floor(rng() * vantages.length)];
  const B = Math.max(2000, Math.min(2060, hingeYear - vantage));

  const moments = [];
  const add = (age, text, tone, eventIndex) => {
    const year = B + age;
    if (year <= endYear && year <= 2100) {
      const m = { year, age, text, tone };
      if (eventIndex !== undefined) m.eventIndex = eventIndex;
      moments.push(m);
    }
  };

  add(0, `${name} is born in ${place} in ${B}.`, 'neutral');

  // Witness moment, pinned directly under the hinge event's card
  const hingeAge = hingeYear - B;
  if (hinge && hingeAge >= 3 && hingeYear <= endYear) {
    let text;
    if (hingeAge <= 9) {
      text = `${first} is ${hingeAge}. ${cap} parents stop explaining the news that year.`;
    } else if (hingeAge <= 17) {
      text = `${first} is ${hingeAge} — old enough to follow it live, too young to do anything about it.`;
    } else if (hingeAge <= 29) {
      text = `${first} is ${hingeAge}. ${cap} plans were made for a different decade.`;
    } else if (hingeAge <= 55) {
      text = `${first} is ${hingeAge}. At home the questions are practical: stock up, move, or stay.`;
    } else {
      text = `${first} is ${hingeAge} and has seen versions of this before — not at this scale.`;
    }
    add(hingeAge, text, 'bad', hingeIdx);
  }

  let s = stateAt(tl, B + 5);
  if (s.conflict_deaths - stateAt(tl, B).conflict_deaths > 100000 || s.us_polarization > 0.5) {
    add(5, `${first} starts school. There is a new security gate at the entrance; the parents talk about the news while they wait.`, 'bad');
  } else {
    add(5, `${first} starts school. The news that year is mostly somewhere else.`, 'good');
  }

  s = stateAt(tl, B + 13);
  if (s.social_media_penetration > 0.4 && s.misinformation_severity > 0.4) {
    add(13, `${first} gets a first phone at thirteen. ${cap} class regularly can't agree on what happened last week.`, 'bad');
  } else if (s.internet_freedom_index < 0.4) {
    add(13, `${first} gets a first phone at thirteen — filtered, licensed, logged. Certain searches are understood to be unwise.`, 'bad');
  } else {
    add(13, `${first} gets a first phone at thirteen. The network ${pron} grows up on is still mostly open.`, 'good');
  }

  s = stateAt(tl, B + 18);
  const sPrev = stateAt(tl, B + 14);
  if (s.conflict_deaths - sPrev.conflict_deaths > 150000) {
    add(18, `${first} turns eighteen with a war on. Two classmates enlist after graduation; ${pron} doesn't.`, 'bad');
  } else if (s.global_gdp_growth_modifier < 0.95) {
    add(18, `${first} graduates into a recession and starts university on loans and a warehouse job.`, 'bad');
  } else {
    add(18, `${first} graduates and leaves ${city} for university, the first in the family to go far for it.`, 'good');
  }

  s = stateAt(tl, B + 24);
  if (s.automation_displacement > 0.25) {
    add(24, `${first} retrains twice before twenty-five. The job ${pron} studied for is done by software now; the new job is checking the software's work.`, 'bad');
  } else if (s.ai_development_year_offset > 5) {
    add(24, `${first} takes a first job where most of the output is machine-drafted. Reviewing it pays less than writing it used to.`, 'neutral');
  } else {
    add(24, `${first} lands a first job. Commutes, deadlines, rent. Nothing about it would surprise ${poss} grandparents.`, 'good');
  }

  s = stateAt(tl, B + 31);
  if (s.climate_temp_anomaly > 1.6 || s.food_security_index < 0.6) {
    add(31, `${first} and ${poss} partner put off having a child for three years; the summers and the food prices are both part of that decision. A daughter arrives in ${B + 31} anyway.`, 'bad');
  } else {
    add(31, `${first} has a daughter in ${B + 31}. She will be ${2100 - (B + 31)} when the century ends.`, 'good');
  }

  s = stateAt(tl, B + 45);
  if (s.sea_level_rise_meters > 0.5 || s.climate_temp_anomaly > 2.2) {
    add(45, `At forty-five, ${first} helps ${poss} parents move inland. The third flood in a decade settled what the insurance premiums had started.`, 'bad');
  } else if (s.renewable_energy_share > 0.6) {
    add(45, `At forty-five, ${first} notes what didn't happen: the collapse predicted for ${poss} generation. The grid finished going green while ${pron} was in ${poss} thirties.`, 'good');
  } else {
    add(45, `At forty-five, ${first} lives in a climate better than feared and worse than promised.`, 'neutral');
  }

  s = stateAt(tl, B + 55);
  const d0 = stateAt(tl, B).global_democracy_index;
  if (s.global_democracy_index > d0 + 0.1) {
    add(55, `${first}'s daughter votes in her first election, in a world the indices rate as freer than the one ${first} was born into.`, 'good');
  } else if (s.global_democracy_index < d0 - 0.1) {
    add(55, `${first}'s daughter casts her first vote already knowing the result. ${first} remembers when the counting took days and the outcome was in doubt.`, 'bad');
  }

  s = stateAt(tl, B + 65);
  if (s.inequality_index > 0.65) {
    add(65, `${first} turns sixty-five and keeps working, like most people ${pron} knows.`, 'bad');
  } else {
    add(65, `${first} retires at sixty-five. The pension holds.`, 'good');
  }

  const sEnd = stateAt(tl, endYear);
  if (cutShort) {
    const final = events[events.length - 1];
    const firstClause = (final.description || '').split('.')[0];
    add(endYear - B, `${first} is ${endYear - B} in ${endYear}. ${firstClause}. The record ends there.`, 'bad');
  } else {
    const lifeExp = 79 + sEnd.us_life_expectancy_delta * 0.7;
    const deathAge = Math.floor(lifeExp + rng() * 6);
    if (B + deathAge >= 2100) {
      add(2100 - B, `${first} is ${2100 - B} when the century ends — the simulation stops; ${pron} doesn't.`, 'good');
    } else {
      const extra = Math.max(0, Math.floor(lifeExp - 79));
      add(deathAge, `${first} dies in ${B + deathAge}, at ${deathAge} — ${extra} years past the life expectancy of the world ${pron} was born into.`, 'neutral');
    }
  }

  moments.sort((a, b) => a.year - b.year || a.age - b.age);
  return { profile: { name, hometown: place, birthYear: B }, moments };
}
