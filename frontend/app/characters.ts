import roster from "../../gameplay/characters.json"

export interface Character {
  UID: string
  Character: string
  Description: string
  Charisma: number
  Intellect: number
  Stubbornness: number
  Empathy: number
  "Influence Range": number
  Loyalty: number
  Curiosity: number
  Consistency: number
}

const player = (UID: string, Character: string): Character => ({
  UID, Character, Description: "Human player", Charisma: 0, Intellect: 0,
  Stubbornness: 0, Empathy: 0, "Influence Range": 0, Loyalty: 0, Curiosity: 0, Consistency: 0,
})
const characters: Character[] = [...roster, player("player_red", "Player Red"), player("player_blue", "Player Blue")]
export default characters
