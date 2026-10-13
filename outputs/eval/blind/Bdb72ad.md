# PantryPal discovery brief

## 1. Recommendation
We recommend to test further before committing to build PantryPal [idea_brief]. Core consumer pains around food waste and the mental effort of dinner decisions are real, but the core mechanism—maintaining an up-to-date pantry inventory to power a rigid weekly plan—faces severe friction [P01:t8, P02:t8, P05:t1, P05:t4]. Furthermore, willingness to pay is unvalidated and narrow, requiring proof of low-effort input and flexible planning before software development begins [P01:t9, P02:t9, P03:t9, P05:t9, S05].

## 2. Who the users are
The idea brief defines the target as households of two or more people who cook at home on most weeknights [idea_brief]. In research, this definition conflates household size with cooking routines and problem severity [P01, P02, P03, P04, P05, P07, P08, P09, P10].

- Busy working families with children (In-target; 3 interviews evaluated, raw count 3, weighted count 2.40: P01 [weight 1.00], P03 [weight 0.70], P04 [weight 0.70]): High dinner friction, high mental load, weekly or bulk shopping with top-ups [P01:t1, P01:t5, P03:t5, P04:t1, P04:t5]. (Note: P06 was excluded due to extreme interviewer bias [P06]).
- Working couples without children (In-target / partial fit; 3 interviews, raw count 3, weighted count 1.90: P02 [weight 0.90, in-target], P05 [weight 0.50, partial fit], P08 [weight 0.50, partial fit]): Cook regularly but have irregular hours or uncoordinated shopping, resulting in spoiled produce [P02:t2, P05:t1, P05:t2, P08:t2].
- Predictable routine retirees (In-target; 1 interview, raw count 1, weighted count 0.90: P09 [weight 0.90]): Cook daily at home, but have decades-old stable habits and lack the problem [P09:t1, P09:t2].
- Flatmates (Adjacent / partial fit; 1 interview, raw count 1, weighted count 0.50: P10 [weight 0.50]): Cook individually with shared kitchen supplies, causing inventory clashes [P10:t1, P10:t2].
- Solo dwellers (Out of target; 1 interview, raw count 1, weighted count 0.25: P07 [weight 0.25]): Rarely cook and do not experience dinner planning friction [P07:t1, P07:t2].

User segmentation by shopping rhythm is more predictive than household size alone: weekly bulk shoppers match weekly planning tools, whereas daily ad-hoc shoppers struggle with predefined weekly structures [P01:t5, P03:t5, P04:t5, P05:t1, P05:t5, P09:t5].

## 3. Problems that are real
- Food waste from forgotten fridge items: Supported across 5 usable interviews (raw count 5 of 9 non-excluded, evidence-weighted count 3.60 of 5.60; families 2 of 3, couples 2 of 3, flatmates 1 of 1). In working families, P01 reported: "Last week I bought a big bag of spinach for a recipe I never made. It went slimy in the drawer and I felt terrible about it." [P01:t4]. In couples, P02 reported: "We throw away so much food. Half a cucumber, wilted herbs, yoghurt that expired last week." [P02:t2]. In flatmates, P10 reported: "Nobody remembers what we already have, so we buy duplicates and then one of them goes bad." [P10:t2]. Market research confirms households discard 19% of purchased food [S01].
- Mental load and daily decision fatigue: Supported across 4 usable interviews (raw count 4 of 9 non-excluded, evidence-weighted count 3.10 of 5.60; families 3 of 3, couples 1 of 3). P01 reported: "It's the mental load. Every single day somebody has to decide what's for dinner, and that somebody is me." [P01:t2]. P04 stated: "The worst part is the daily question of what to cook. By Wednesday I have no ideas left." [P04:t2]. However, P03 presented an internal contradiction: stating "Planning is my favourite part of the week, honestly. I would never want an app to take that away from me." [P03:t1], while also stating "Deciding is exhausting. I would rather cook anything than think about what to cook." [P03:t2]. General adults spend 22 minutes daily deciding what to cook, based on 2023 data [S04].
- Uncoordinated household shopping causing duplicate purchases: Supported across 3 usable interviews (raw count 3 of 9 non-excluded, evidence-weighted count 2.10 of 5.60; couples 1 of 3, families 1 of 3, flatmates 1 of 1). P02 stated: "We bought basil twice in one week because each of us thought we were out. Both went bad." [P02:t4]. P04 reported: "My wife bought chicken and I bought chicken, the same afternoon. We ended up with six breasts and a freezer that was already full." [P04:t4]. P10 experienced similar duplicate purchases [P10:t2].

## 4. What the evidence says
- Behaviour vs stated preference: Participants actively maintain grocery lists via notes apps, shared list apps, or paper pads, but no participant maintains an active pantry inventory [P01:t6, P02:t6, P03:t6, P04:t6, P09:t6, P10:t6]. Participants state an aversion to manual data entry; P02 stated: "Setup has to be fast. If I need to type in my whole pantry I'll quit on day two." [P02:t8] (identical templated phrasing repeated in P05:t8, P07:t8, P10:t8). Furthermore, P05 demonstrated behavioral failure with rigid tools: "I tried a meal-planning app once. By Thursday I hadn't followed the plan and I just stopped opening it." [P05:t4].
- Stated constraints on planning tools: Users insist on control and quick prep. P01 stated: "Recipes must be realistic for weeknights. Thirty minutes at most. I want to edit the plan easily. I don't want an app dictating to me." [P01:t8] (shared with P02:t8, P03:t8, P04:t8). In families, allergy and taste constraints dominate; P03 stated: "It would need to understand allergies and what we actually like, otherwise it's just noise." [P03:t8] (shared with P04:t8).
- Willingness to pay: Stated intent is contingent and modest, ranging from free with ads to 5 or 6 euros per month [P01:t9, P02:t9, P03:t9, P05:t9, P09:t9, P10:t9]. P01 noted: "A few euros a month, maybe, if it clearly saves me money on groceries." [P01:t9]. P02 stated: "Maybe five or six euros. More than that and I'd just keep my notes app." [P02:t9]. P08 offered an outlier stated figure of "thirty euros a month, easy" [P08:t9], but this was anchored on an extreme one-time holiday spoilage event [P08:t2, P08:t4]. P05, P07, and P09 stated they would not pay and require a free tier [P05:t9, P07:t9, P09:t9]. Market data shows median stated willingness to pay for a cooking app is EUR 3.50 per month [S05].
- Conflicting evidence and methodological caveats: P09 reported a 40-year fixed routine with no need for apps ("we have never needed one" [P09:t1]), yet later claimed shopping is handled "Both of us, but not in a coordinated way." [P09:t7]. Interview P04 contained attribution inconsistency, referencing both my wife and my husband [P04:t2, P04:t7]. Interview P06 was entirely leading and provided zero usable evidence [P06].

## 5. Competitors and market
- Competitor landscape:
  - MealLoop: Weekly meal planner with automatic grocery lists, diet filters, and family sharing at EUR 6.99/month or EUR 49.99/year; targets families (verified 2026-07-30) [C:MealLoop].
  - PantryGenie: Pantry inventory tracker with barcode scanning, expiry alerts, and shopping list at EUR 3.99/month; targets waste reduction (verified 2026-06-18) [C:PantryGenie].
  - FridgeChef: Recipe suggestions from fridge photos with free ad-supported tier or EUR 4.99/month premium; targets improvisers (verified 2026-08-12) [C:FridgeChef].
  - SupperSync: Shared dinner planner, who-cooks rota, and shared list at EUR 4.49/month per household; targets shared households (verified 2026-08-25) [C:SupperSync].
  - PlanPlate: Simple meal planning calendar at EUR 2.99/month (verified 2024-11-05; possibly outdated) [C:PlanPlate].
  - ZeroWaste Kitchen: Use-it-up leftover recipes, free/donation-supported (verified 2025-01-20; possibly outdated) [C:ZeroWaste Kitchen].
  - WeekWise: Budget-focused meal plans with free tier and EUR 29.99 one-off pack (verified 2026-05-02; source URL missing / unsourced) [C:WeekWise].
- Differentiation analysis: The idea brief claims existing apps do not know what you already own [idea_brief]. This claim is contradicted by PantryGenie and FridgeChef, which track inventory or fridge contents [C:PantryGenie, C:FridgeChef]. True differentiation lies strictly in the combination of inventory awareness with automated weekly meal planning and shopping list generation [idea_brief, C:MealLoop, C:PantryGenie].
- Market baseline: Two-person households spend an average of EUR 118 per week on groceries [S02]. Only 11% of households currently use a meal-planning app [S03]. Cooking app median willingness to pay is EUR 3.50 per month [S05]. Current competitor pricing establishes an active market band between EUR 2.99 and EUR 6.99 per month [C:PlanPlate, C:MealLoop].

## 6. Risks and open assumptions
- Critical assumption 1 (Highest risk): Households will keep an inventory up to date. Users drop apps when manual entry is required [P02:t8, P05:t4]. No interviewed participant currently tracks inventory digitally [P01:t6, P02:t6, P03:t6, P04:t6].
- Critical assumption 2: A weekly plan format matches household reality. Irregular work hours and sudden fatigue make rigid weekly schedules break down by mid-week [P01:t3, P02:t3, P05:t1, P05:t4]. Same-day dinner suggestions may be necessary [P05:t1, P08:t1].
- Critical assumption 3: Willingness to pay at sustainable margins. Users benchmark against free notes apps and expect concrete grocery savings before paying EUR 3.00 to EUR 5.00 monthly [P01:t9, P02:t9, S05].
- Critical assumption 4: Target definition validity. Defining target users simply as households of 2+ cooking weeknights includes segments like routine retirees who lack the problem entirely [idea_brief, P09:t1, P09:t2].
- Technical and operational risks: Recipe generation must support strict under-30-minute weeknight execution, selective child preferences, and dietary restrictions without manual friction [P01:t8, P03:t8, P04:t3, P04:t8].

## 7. What to test next
- Experiment 1: Low-effort inventory onboarding prototype (Concierge / Wizard of Oz)
  - Test whether users will log baseline fridge/pantry items via receipt scanning, photo snapping, or quick-select onboarding lists rather than typing.
  - Metric: Onboarding completion rate >= 65% and inventory updated after 5 days >= 40% (Sample size proposed: 50 target households) [UNSUPPORTED].
- Experiment 2: Weekly plan vs. same-day flexible suggestion test
  - Compare engagement between two cohorts: Cohort A receives a fixed 5-day dinner plan; Cohort B receives a dynamic tonight suggestion based on on-hand perishables.
  - Metric: Cohort plan adherence / recipe completion rate >= 50% on day 4 (Sample size proposed: 60 households, 30 per arm) [UNSUPPORTED].
- Experiment 3: Willingness-to-pay landing page test
  - Test acquisition messaging highlighting grocery savings and reduced waste at price points of EUR 3.49/month and EUR 4.99/month.
  - Metric: Pre-order / email waitlist conversion rate >= 5% on paid plan call-to-action (Sample size proposed: 500 landing page visits) [UNSUPPORTED].

## 8. Unsupported or weak claims
- Claim: Households argue about what is for dinner and PantryPal will stop arguments [idea_brief]. Weakly supported; documented in only 1 couple turn [P02:t3]. Most evidence shows internal individual fatigue or shopping coordination disconnects rather than domestic conflict [P01:t2, P02:t2, P04:t2, P04:t4, P10:t2].
- Claim: Existing recipe apps do not know what you already own [idea_brief]. Contradicted by C:PantryGenie and C:FridgeChef [C:PantryGenie, C:FridgeChef].
- Claim: Annual market growth rate of 25% for meal planning apps [S06]. Marked unsupported due to missing source and date [S06].
- Claim: 73% of families struggle with dinner decisions [S07]. Marked unsupported due to missing source and date [S07].
- Claim: 97% of households would pay for automated meal planning [S08]. Marked unreliable; blog source [S08].
- Claim: 4% of grocery purchases are made online [S09]. Marked stale (2016 retail survey) [S09].
- Claim: Willingness to pay of EUR 30 per month [P08:t9]. Outlier response tied to a single vacation incident, unrepresentative of routine dinner planning [P08:t2, P08:t4, P08:t9].
