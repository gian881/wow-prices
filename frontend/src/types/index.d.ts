export type Quality =
  | 'normal'
  | 'tier_1'
  | 'tier_2'
  | 'tier_3'
  | 'tier_4'
  | 'tier_5'
  | 'tier_1_midnight'
  | 'tier_2_midnight'

export type Rarity = 'COMMON' | 'UNCOMMON' | 'RARE' | 'EPIC' | 'LEGENDARY' | 'ARTIFACT' | 'TOKEN'

export type GoldAndSilver = {
  gold: number
  silver: number
}

export type Intent = 'buy' | 'sell' | 'both'
