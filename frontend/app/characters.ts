export interface Character {
  "UID": string
  "Character": string
  "Description": string
  "Charisma": number
  "Intellect": number
  "Stubbornness": number
  "Empathy": number
  "Influence Range": number
  "Loyalty": number
  "Curiosity": number
  "Consistency": number
}

const json: Character[] = [
  {
    "UID": "elon_musk",
    "Character": "Elon Musk",
    "Description": "Tech entrepreneur, SpaceX and Tesla founder",
    "Charisma": 8,
    "Intellect": 9,
    "Stubbornness": 8,
    "Empathy": 5,
    "Influence Range": 9,
    "Loyalty": 6,
    "Curiosity": 10,
    "Consistency": 7
  },
  {
    "UID": "mahatma_gandhi",
    "Character": "Mahatma Gandhi",
    "Description": "Indian independence leader, non-violence advocate",
    "Charisma": 9,
    "Intellect": 8,
    "Stubbornness": 7,
    "Empathy": 10,
    "Influence Range": 10,
    "Loyalty": 9,
    "Curiosity": 7,
    "Consistency": 9
  },
  {
    "UID": "winston_churchill",
    "Character": "Winston Churchill",
    "Description": "British PM during WWII, famed orator",
    "Charisma": 9,
    "Intellect": 8,
    "Stubbornness": 9,
    "Empathy": 6,
    "Influence Range": 9,
    "Loyalty": 8,
    "Curiosity": 7,
    "Consistency": 8
  },
  {
    "UID": "marie_curie",
    "Character": "Marie Curie",
    "Description": "Pioneering physicist, discovered radium",
    "Charisma": 6,
    "Intellect": 10,
    "Stubbornness": 7,
    "Empathy": 7,
    "Influence Range": 7,
    "Loyalty": 9,
    "Curiosity": 10,
    "Consistency": 9
  },
  {
    "UID": "nelson_mandela",
    "Character": "Nelson Mandela",
    "Description": "Anti-apartheid revolutionary, SA President",
    "Charisma": 10,
    "Intellect": 8,
    "Stubbornness": 8,
    "Empathy": 9,
    "Influence Range": 10,
    "Loyalty": 9,
    "Curiosity": 8,
    "Consistency": 9
  },
  {
    "UID": "bill_gates",
    "Character": "Bill Gates",
    "Description": "Microsoft co-founder, philanthropist",
    "Charisma": 7,
    "Intellect": 10,
    "Stubbornness": 7,
    "Empathy": 7,
    "Influence Range": 8,
    "Loyalty": 8,
    "Curiosity": 9,
    "Consistency": 8
  },
  {
    "UID": "albert_einstein",
    "Character": "Albert Einstein",
    "Description": "Physicist, E=mc² fame",
    "Charisma": 7,
    "Intellect": 10,
    "Stubbornness": 6,
    "Empathy": 7,
    "Influence Range": 8,
    "Loyalty": 7,
    "Curiosity": 10,
    "Consistency": 8
  },
  {
    "UID": "martin_luther",
    "Character": "Martin Luther King Jr.",
    "Description": "Civil rights leader, \"I Have a Dream\" speech",
    "Charisma": 10,
    "Intellect": 9,
    "Stubbornness": 8,
    "Empathy": 10,
    "Influence Range": 10,
    "Loyalty": 9,
    "Curiosity": 8,
    "Consistency": 9
  },
  {
    "UID": "queen_elizabeth",
    "Character": "Queen Elizabeth I",
    "Description": "Tudor monarch, led English Golden Age",
    "Charisma": 8,
    "Intellect": 9,
    "Stubbornness": 8,
    "Empathy": 6,
    "Influence Range": 9,
    "Loyalty": 8,
    "Curiosity": 7,
    "Consistency": 8
  },
  {
    "UID": "napoleon_bonaparte",
    "Character": "Napoleon Bonaparte",
    "Description": "French emperor, military genius",
    "Charisma": 9,
    "Intellect": 9,
    "Stubbornness": 9,
    "Empathy": 4,
    "Influence Range": 10,
    "Loyalty": 7,
    "Curiosity": 8,
    "Consistency": 8
  },
  {
    "UID": "donald_trump",
    "Character": "Donald Trump",
    "Description": "Businessman, 45th US President",
    "Charisma": 8,
    "Intellect": 6,
    "Stubbornness": 10,
    "Empathy": 3,
    "Influence Range": 9,
    "Loyalty": 5,
    "Curiosity": 4,
    "Consistency": 5
  },
  {
    "UID": "steve_jobs",
    "Character": "Steve Jobs",
    "Description": "Apple co-founder, iPhone creator",
    "Charisma": 9,
    "Intellect": 9,
    "Stubbornness": 9,
    "Empathy": 5,
    "Influence Range": 9,
    "Loyalty": 7,
    "Curiosity": 10,
    "Consistency": 7
  },
  {
    "UID": "benito_mussolini",
    "Character": "Benito Mussolini",
    "Description": "Italian fascist dictator",
    "Charisma": 8,
    "Intellect": 7,
    "Stubbornness": 9,
    "Empathy": 2,
    "Influence Range": 8,
    "Loyalty": 6,
    "Curiosity": 4,
    "Consistency": 7
  },
  {
    "UID": "julius_caesar",
    "Character": "Julius Caesar",
    "Description": "Roman general, \"I came, I saw, I conquered\"",
    "Charisma": 9,
    "Intellect": 9,
    "Stubbornness": 8,
    "Empathy": 5,
    "Influence Range": 10,
    "Loyalty": 7,
    "Curiosity": 8,
    "Consistency": 8
  },
  {
    "UID": "mother_teresa",
    "Character": "Mother Teresa",
    "Description": "Catholic nun, served poor in Calcutta",
    "Charisma": 8,
    "Intellect": 6,
    "Stubbornness": 7,
    "Empathy": 10,
    "Influence Range": 8,
    "Loyalty": 10,
    "Curiosity": 5,
    "Consistency": 9
  },
  {
    "UID": "genghis_khan",
    "Character": "Genghis Khan",
    "Description": "Mongol emperor, largest land empire",
    "Charisma": 9,
    "Intellect": 8,
    "Stubbornness": 9,
    "Empathy": 2,
    "Influence Range": 10,
    "Loyalty": 7,
    "Curiosity": 7,
    "Consistency": 8
  },
  {
    "UID": "leonardo_davinci",
    "Character": "Leonardo da Vinci",
    "Description": "Renaissance polymath, painted Mona Lisa",
    "Charisma": 7,
    "Intellect": 10,
    "Stubbornness": 6,
    "Empathy": 7,
    "Influence Range": 7,
    "Loyalty": 8,
    "Curiosity": 10,
    "Consistency": 8
  },
  {
    "UID": "margaret_thatcher",
    "Character": "Margaret Thatcher",
    "Description": "UK's first female PM, \"Iron Lady\"",
    "Charisma": 8,
    "Intellect": 8,
    "Stubbornness": 10,
    "Empathy": 4,
    "Influence Range": 9,
    "Loyalty": 8,
    "Curiosity": 6,
    "Consistency": 9
  },
  {
    "UID": "mao_zedong",
    "Character": "Mao Zedong",
    "Description": "Chinese communist leader",
    "Charisma": 8,
    "Intellect": 8,
    "Stubbornness": 10,
    "Empathy": 3,
    "Influence Range": 10,
    "Loyalty": 7,
    "Curiosity": 5,
    "Consistency": 7
  },
  {
    "UID": "rosa_parks",
    "Character": "Rosa Parks",
    "Description": "Sparked Montgomery Bus Boycott",
    "Charisma": 7,
    "Intellect": 7,
    "Stubbornness": 9,
    "Empathy": 9,
    "Influence Range": 8,
    "Loyalty": 10,
    "Curiosity": 7,
    "Consistency": 10
  },
  {
    "UID": "william_shakespeare",
    "Character": "William Shakespeare",
    "Description": "English playwright, wrote \"Romeo and Juliet\"",
    "Charisma": 8,
    "Intellect": 10,
    "Stubbornness": 6,
    "Empathy": 8,
    "Influence Range": 9,
    "Loyalty": 7,
    "Curiosity": 10,
    "Consistency": 8
  },
  {
    "UID": "gary_marcus",
    "Character": "Gary Marcus",
    "Description": "AI critic, cognitive scientist",
    "Charisma": 6,
    "Intellect": 9,
    "Stubbornness": 8,
    "Empathy": 6,
    "Influence Range": 7,
    "Loyalty": 8,
    "Curiosity": 9,
    "Consistency": 8
  },
  {
    "UID": "hunter_thompson",
    "Character": "Hunter S. Thompson",
    "Description": "Gonzo journalist, \"Fear and Loathing\" author",
    "Charisma": 8,
    "Intellect": 9,
    "Stubbornness": 9,
    "Empathy": 6,
    "Influence Range": 8,
    "Loyalty": 5,
    "Curiosity": 10,
    "Consistency": 6
  },
  {
    "UID": "player_red",
    "Character": "Player Red",
    "Description": "You are Player Red",
    "Charisma": 5,
    "Intellect": 5,
    "Stubbornness": 5,
    "Empathy": 5,
    "Influence Range": 5,
    "Loyalty": 5,
    "Curiosity": 5,
    "Consistency": 5
  },
  {
    "UID": "player_blue",
    "Character": "Player Blue",
    "Description": "You are Player Blue",
    "Charisma": 5,
    "Intellect": 5,
    "Stubbornness": 5,
    "Empathy": 5,
    "Influence Range": 5,
    "Loyalty": 5,
    "Curiosity": 5,
    "Consistency": 5
  }
]

export default json
