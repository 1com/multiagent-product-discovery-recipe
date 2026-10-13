# PantryPal discovery brief

## 1. Recommendation
We recommend testing further before building a full product. Evidence indicates that dinner decision fatigue, household shopping misalignment, and food waste are genuine problems for busy households, but keeping an inventory up to date presents high friction [P01:t2, P02:t2, P02:t8]. Furthermore, weekly planning suits structured weekly shoppers but alienates flexible or daily shoppers, and willingness to pay remains low and conditional [P01:t5, P01:t9, P05:t1, P05:t5, S05]. We must de-risk low-effort inventory tracking and test format fit before writing production code.

## 2. Who the users are
The idea brief defines the target customer as households of two or more people who cook at home on most weeknights [idea_brief]. Across 10 research participants (5 target-fit, 3 partial-fit adjacent, 1 out-of-target, 1 excluded), the problem space divides into distinct sub-segments:
- Busy families with children (Target fit: 3 usable interviews: P01 primary weight 1.00; P03 supporting weight 0.70; P04 supporting weight 0.70; plus P06 excluded weight 0.00): Cook regularly out of necessity, face intense time constraints, and carry heavy cognitive planning burdens [P01:t1, P03:t1, P04:t1]. Weekly shopping with top-ups is common [P01:t5, P03:t5, P04:t5].
- Dual-income couples without children (Target fit: 2 usable interviews: P02 primary weight 0.90; P09 primary weight 0.90): Experienced cooks with fixed decades-old routines (P09, 1 of 2 target couples) report no acute frustration and buy as they go [P09:t1, P09:t2, P09:t5]. In contrast, long-hours working couples (P02, 1 of 2 target couples) suffer from uncoordinated shopping and mid-week exhaustion [P02:t1, P02:t2, P02:t7].
- Irregular-schedule or travelling couples (Adjacent partial-fit: 2 interviews: P05 weight 0.50; P08 weight 0.50): Work from home or travel, shop day to day, and find strict planning stressful [P05:t1, P05:t5, P08:t1, P08:t3].
- Flatmates sharing a kitchen (Adjacent partial-fit: 1 interview: P10 weight 0.50): Cook individually on weeknights but share staples, experiencing friction around duplicate purchases and unreplaced items [P10:t1, P10:t2].
- Solo dwellers / students (Out-of-target: 1 interview: P07 weight 0.25): Rare home cooking, purchases small amounts, and has no coordination need [P07:t1, P07:t2].

## 3. Problems that are real
- Food waste from forgotten fridge items: Supported across segments by past behaviour in 5 of 8 usable multi-person interviews (raw count: 5 of 8; weighted count: 3.60 of 5.40; P01, P02, P03, P05, P08). P01 threw away spinach: "Last week I bought a big bag of spinach for a recipe I never made. It went slimy in the drawer and I felt terrible about it." [P01:t4]. P02 bought duplicate herbs: "We bought basil twice in one week because each of us thought we were out. Both went bad." [P02:t4]. Market data confirms that households discard roughly 19% of the food they buy [S01].
- Daily dinner decision fatigue: Supported by past behaviour and unprompted reflections in 4 of 8 usable multi-person interviews (raw count: 4 of 8; weighted count: 3.10 of 5.40; P01, P02, P04, P05). P01 ended up with fish fingers when unplanned: "Last Tuesday I picked up the kids at five, we got home at six, and I realised at six that I had nothing planned. I made fish fingers and frozen peas, again." [P01:t3]. In P04, "The worst part is the daily question of what to cook. By Wednesday I have no ideas left." [P04:t2]. An older time-use study notes adults spend 22 minutes each day deciding what to cook, though this benchmark is from 2023 [S04].
- Uncoordinated household shopping causing duplicate purchases: Supported by past behaviour in 3 of 8 usable multi-person interviews (raw count: 3 of 8; weighted count: 2.10 of 5.40; P02, P04, P10). P04 experienced: "My wife bought chicken and I bought chicken, the same afternoon. We ended up with six breasts and a freezer that was already full." [P04:t4]. P10 reported: "Nobody remembers what we already have, so we buy duplicates and then one of them goes bad." [P10:t2].

## 4. What the evidence says
- Behaviour versus stated preference: While food waste and duplicate shopping are demonstrated through concrete past events [P01:t4, P02:t4, P04:t4], stated willingness to adopt an automated plan is heavily constrained by requirements [P01:t8, P02:t8, P03:t8]. Users require quick weeknight meals ("Thirty minutes at most." [P01:t8, P04:t8]) and full control ("I want to edit the plan easily. I don't want an app dictating to me." [P01:t8, P02:t8, P03:t8, P05:t8]).
- Templated friction warnings: Across 5 distinct interviews (raw count: 5 of 8; weighted count: 3.10 of 5.40; P02, P05, P07, P08, P10), participants identically warned: "Setup has to be fast. If I need to type in my whole pantry I'll quit on day two." [P02:t8, P05:t8, P07:t8, P08:t8, P10:t8]. Inventory setup and upkeep is an extreme retention risk [P02:t8, P10:t8].
- Conflicting evidence within interviews:
  - P03 exhibits a major contradiction: P03 states "Planning is my favourite part of the week, honestly. I would never want an app to take that away from me." [P03:t1], yet also asserts "Deciding is exhausting. I would rather cook anything than think about what to cook." [P03:t2]. Confidence is reduced; P03 enjoys ritual planning but hates operational meal decisions.
  - P04 displays attribution inconsistency: The persona notes a wife who buys without checking [P04:t2, P04:t4], but later states decision-makers are "Me, my husband and, loudly, three children." [P04:t7]. Confidence is lowered due to potential multi-speaker transcript mixing.
  - P02 shows minor tool inconsistency, citing "We use a shared list app, but it's only a list." [P02:t6], but later stating "More than that and I'd just keep my notes app." [P02:t9].
  - P09 exhibits minor routine inconsistency, stating they shop at the same stall weekly [P09:t3], yet also saying "I go to the shop almost every day and buy as I go." [P09:t5], and claiming a stable 40-year routine [P09:t1] while noting shopping occurs "Both of us, but not in a coordinated way." [P09:t7].
- Research method exclusions: Interview P06 is excluded from evidence weighting (weight 0.00) because questions were aggressively leading (e.g. "Don't you find it really frustrating not knowing what to cook every day?" [P06:t2]) and P06 repeated answers word-for-word from P01 [P01:t1, P06:t1]. P06 provides zero customer claim support.
- Stated willingness to pay (WTP): WTP is unvalidated. 5 participants stated a guarded willingness between a few euros and 6 euros per month, strictly conditioned on savings [P01:t9, P02:t9, P04:t9, P10:t9] or waste reduction [P03:t9]. Multiple participants demanded a free version [P03:t9, P05:t9, P07:t9, P09:t9]. P08 offered an outlier of EUR 30/month [P08:t9], which was anchored on a single holiday spoil incident of EUR 200 of food [P08:t2] and must be excluded from typical estimates. Realistic monthly WTP lies between EUR 0 and EUR 6 [P01:t9, P02:t9, P05:t9].

## 5. Competitors and market
- Existing landscape contradicts the idea brief: The idea brief claims recipe apps do not know what you already own [idea_brief], but competitors already offer inventory tracking and use-up suggestions:
  - FridgeChef (last verified: 2026-08-12): Suggests recipes from photos of your fridge; free with ads, or premium at EUR 4.99/month [C:FridgeChef].
  - PantryGenie (last verified: 2026-06-18): Pantry inventory tracker with barcode scanning and expiry alerts at EUR 3.99/month [C:PantryGenie].
  - MealLoop (last verified: 2026-07-30): Weekly meal planner with automatic grocery lists at EUR 6.99/month or EUR 49.99/year [C:MealLoop].
  - SupperSync (last verified: 2026-08-25): Shared dinner planner with chore rotas and shared lists at EUR 4.49/month per household [C:SupperSync].
  - ZeroWaste Kitchen (last verified: 2025-01-20): Leftover use-it-up recipes, free/donation; note that verification data is over 18 months old and may be outdated [C:ZeroWaste Kitchen].
  - PlanPlate (last verified: 2024-11-05): Meal planning calendar at EUR 2.99/month; note that verification data is from late 2024 and may be outdated [C:PlanPlate].
  - WeekWise (last verified: 2026-05-02): Budget meal plans at EUR 29.99 one-off; source URL is missing, so specific details remain unsourced [C:WeekWise].
- Differentiation: True differentiation cannot be inventory tracking alone (already done by PantryGenie [C:PantryGenie]) or weekly planning alone (already done by MealLoop [C:MealLoop]), but rather the seamless combination of inventory awareness and flexible weekly planning [C:MealLoop, C:PantryGenie].
- Market context: 11% of households currently use a meal-planning app [S03]. Two-person households spend an average of EUR 118 weekly on groceries [S02]. The median stated willingness to pay for a cooking app is EUR 3.50 per month [S05]. Pricing hypotheses must stay within the market band of EUR 2.99 to EUR 6.99/month [C:PlanPlate, C:MealLoop, S05].

## 6. Risks and open assumptions
- Riskiest assumption: Households will keep a pantry and fridge inventory up to date in an app [P02:t8, P08:t8, P10:t8]. Multiple users explicitly noted they will abandon the app on day two if manual inventory entry is required [P02:t8, P05:t8, P08:t8, P10:t8].
- Format mismatch (Weekly plan vs. Daily improvisation): A fixed weekly plan does not fit all households [P02:t10, P05:t1]. Flexible cooks and daily shoppers experience anxiety when plans fail ("A plan I don't follow feels like failure, so I decide on the day." [P05:t1, P05:t4]).
- Shopping rhythm segmentation: Weekly planning with an automated shopping list primarily serves weekly shoppers (e.g. P01 online weekly [P01:t5]; P03, P04 Saturday shoppers [P03:t5, P04:t5]), but fails daily shoppers (P05, P09 [P05:t5, P09:t5]).
- Value proposition overstatement ("stop arguing"): The idea brief highlights stopping arguments [idea_brief], but only 1 of 8 usable multi-person interviews reported mealtime arguing (P02 argued for 10 minutes [P02:t3]). The genuine interpersonal friction is shopping coordination and duplicate buying [P02:t2, P04:t2, P04:t4, P10:t2].
- Willingness to pay is fragile: Stated WTP is modest (EUR 3.50 median market benchmark [S05]; EUR 3-6 interview range [P01:t9, P02:t9, P04:t9, P10:t9]) and strictly contingent on saving money [P01:t9, P04:t9, P10:t9]. Any price above EUR 6.99 is untested [C:MealLoop, S05].

## 7. What to test next
- Experiment 1: Low-effort inventory onboarding test (Address Riskiest Assumption).
  - Test whether users will log items via receipt scan, photo, or online basket import versus manual entry [P01:t5, P02:t8, C:FridgeChef].
  - Setup: Concierge or prototype test with 30 target families [UNSUPPORTED].
  - Success metric: At least 60% of households maintain an updated inventory through day 7 [UNSUPPORTED].
- Experiment 2: Weekly plan vs. same-day suggestion test (Address Format Fit).
  - Test whether households complete more home-cooked meals with a rigid 7-day dinner calendar versus an adaptive same-day suggestion based on remaining ingredients [P01:t3, P05:t1, P05:t4].
  - Setup: 2-week split test across 40 busy households [UNSUPPORTED].
  - Success metric: Higher 14-day recipe completion and lower reported food discards in the adaptive group [UNSUPPORTED].
- Experiment 3: Household sync and shared list utility test (Address Coordination).
  - Test whether a real-time shared shopping list prevents duplicate buying across multi-shopper households [P02:t4, P04:t4, P10:t2].
  - Setup: Shared digital list test with 25 multi-person households for 2 weeks [UNSUPPORTED].
  - Success metric: Zero duplicate item purchases reported over 14 days [UNSUPPORTED].
- Experiment 4: Landing page pricing and value proposition test (Address WTP).
  - Test conversion on landing pages offering EUR 3.99/month and EUR 4.99/month with messaging focused on reducing grocery spend and food waste [P01:t9, C:PantryGenie, S05].
  - Setup: Paid traffic test driving 500 visitors per variant [UNSUPPORTED].
  - Success metric: Email pre-order sign-up rate exceeding 5% at EUR 3.99/month [UNSUPPORTED].

## 8. Unsupported or weak claims
- The claim that recipe apps do not know what you already own is contradicted by competitors PantryGenie and FridgeChef [idea_brief, C:FridgeChef, C:PantryGenie].
- The claim that the meal-planning and meal-kit market is growing 25% annually carries no source year or methodology and is unsupported [S06].
- The claim that 73% of families struggle with dinner decisions is unsourced and unsupported [S07].
- The claim that 97% of households would pay for automated meal planning originates from an unreliable blog snippet and is unsupported [S08].
- The statistic that only 4% of grocery purchases are made online is from 2016 and is outdated and unusable [S09].
- P08's stated willingness to pay EUR 30/month is an outlier tied to a single vacation mishap and cannot be generalised [P08:t2, P08:t9].
- The idea brief's claim that couples regularly argue about dinner is weakly supported, appearing in only 1 interview [idea_brief, P02:t3].
