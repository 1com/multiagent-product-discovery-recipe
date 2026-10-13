# PantryPal discovery brief

## 1. Recommendation
We recommend to test further before committing engineering resources to build PantryPal. Discovery reveals genuine pain around dinnertime decision fatigue and food waste across multi-person households, but the concept's core mechanisms face severe friction: users refuse manual pantry tracking and resist rigid automated dinner plans [P01:t8, P02:t8, P05:t4, P05:t8]. We must run targeted prototypes to determine whether a low-effort intake model and flexible planning can achieve viable retention and willingness to pay.

## 2. Who the users are
The idea brief defines target customers as households of two or more people who cook at home on most weeknights [idea_brief]. Across 10 interviews, 9 represent usable non-leading data, while interview P06 is compromised due to leading questions and acquiescence bias [P06:t1, P06:t9].
- Primary segment: Busy working families with children (e.g., P01, P04), who face severe time constraints and conflicting dietary demands [P01:t1, P04:t1].
- Secondary segment: Multi-earner couples without children (e.g., P02, P08), who cook after long hours and experience duplicate shopping or uncoordinated planning [P02:t2, P08:t7].
- Shared flatmates (e.g., P10), who share a kitchen and grocery staples but cook individually and experience coordination friction [P10:t1, P10:t2].
- Non-target segments: Single university students who rarely cook (e.g., P07), and retired couples with entrenched daily cooking routines and no desire for digital planning tools (e.g., P09) [P07:t1, P09:t1].

## 3. Problems that are real
- Daily mental load and decision dread: Deciding what to cook every day causes significant frustration and fatigue [P01:t2, P03:t2, P04:t2, P05:t2]. Adults spend 22 minutes each day deciding what to cook [S04].
- Food waste and discarded perishables: Unused ingredients regularly spoil in refrigerators due to forgotten items and abandoned recipes [P01:t2, P01:t4, P02:t2, P05:t2, P08:t2]. Households discard 19% of the food they buy [S01].
- Household grocery misalignment: Lack of coordination leads to duplicate purchases or missing ingredients for planned dinners [P02:t2, P02:t4, P04:t4, P10:t2].

## 4. What the evidence says
Evidence shows a sharp contrast between observed household behaviour and stated preferences across 9 unbiased interviews:
- Setup friction behaviour: Multiple participants explicitly state they will abandon any service requiring extensive manual inventory entry: "Setup has to be fast. If I need to type in my whole pantry I'll quit on day two." [P02:t8, P05:t8, P07:t8, P08:t8, P10:t8].
- Resistance to automated dictation: Participants want agency rather than rigid plans: "I want to edit the plan easily. I don't want an app dictating to me." [P01:t8, P02:t8, P03:t8, P05:t8]. Rigid meal plans cause guilt and rapid abandonment when schedules deviate [P05:t1, P05:t4]. Conversely, one budget-conscious cook views planning as an enjoyable ritual: "Planning is my favourite part of the week, honestly. I would never want an app to take that away from me." [P03:t1].
- Preparation constraints: Parents emphasize that weekday meals cannot exceed tight time limits: "Recipes must be realistic for weeknights. Thirty minutes at most." [P01:t8, P04:t8].
- Stated willingness to pay: Most receptive participants express modest willingness to pay: "A few euros a month, maybe, if it clearly saves me money on groceries." [P01:t9, P04:t9, P10:t9]. Others expect a free service or refuse to pay altogether [P03:t9, P05:t9, P07:t9, P09:t9]. One participant stated they would pay 30 euros a month after a severe holiday spoilage incident [P08:t2, P08:t9].

## 5. Competitors and market
- Existing competitors cover fragmented aspects of the problem space: FridgeChef offers recipe suggestions from photos of your fridge for EUR 4.99/month [C:FridgeChef]; MealLoop provides weekly meal plans with grocery lists for EUR 6.99/month or EUR 49.99/year [C:MealLoop]; PlanPlate offers a shared calendar for EUR 2.99/month [C:PlanPlate]; PantryGenie provides barcode-based pantry tracking and expiry alerts for EUR 3.99/month [C:PantryGenie]; SupperSync targets shared households with a dinner planner and chore rota for EUR 4.49/month [C:SupperSync]; WeekWise provides budget plans with a EUR 29.99 one-off pack [C:WeekWise]; and ZeroWaste Kitchen provides free leftover recipes [C:ZeroWaste Kitchen].
- Market metrics show that 11% of households currently use a meal-planning app [S03].
- Average weekly grocery spend for a two-person household is EUR 118 [S02].
- Median stated willingness to pay for a cooking app is EUR 3.50 per month [S05].

## 6. Risks and open assumptions
- Onboarding attrition risk: Requiring users to log existing fridge and pantry items creates high initial drop-off [P02:t8, P05:t8, P10:t8].
- Rigid plan churn risk: Automated static weekly plans fail when weeknight chaos intervenes, resulting in user guilt and app abandonment [P05:t1, P05:t4].
- Household sync failure: Multi-member households struggle to maintain shared lists across uncoordinated shoppers [P02:t2, P04:t2, P10:t2].
- Monetization gap: Stated willingness to pay clusters around a few euros per month, near the market median of EUR 3.50 per month, leaving little room for high subscription pricing [P01:t9, P04:t9, S05].

## 7. What to test next
- Experiment 1 (Low-friction pantry onboarding): Test whether photo capture or selecting from a pre-populated staple checklist achieves higher onboarding completion than manual typing. Proposal: Test with 100 busy household cooks, targeting >60% setup completion within 2 minutes [UNSUPPORTED].
- Experiment 2 (Flexible weeknight dinner concierge): Run a 7-day concierge prototype delivering quick under-30-minute recipes based on 3-5 declared perishables, allowing one-click swaps. Proposal: Test with 40 working parents, targeting >70% recipe preparation adherence and daily engagement [UNSUPPORTED].
- Experiment 3 (Paywall and value proposition smoke test): Deploy landing pages testing automated pantry planning at EUR 3.50/month versus grocery waste savings. Proposal: Drive 500 targeted ad clicks, targeting >5% deposit or pre-order conversion rate [UNSUPPORTED].

## 8. Unsupported or weak claims
- The claim from snippet S08 that 97% of households would pay for automated meal planning is an unsubstantiated blog claim that directly contradicts interview behaviour and stated price sensitivity [P01:t9, P05:t9, S05, S08].
- The claim from snippet S06 of 25% annual market growth lacks source and year verification [S06].
- The claim from snippet S07 that 73% of families struggle with dinner decisions lacks source and year verification [S07].
- The claim from snippet S09 that 4% of grocery purchases are made online relies on outdated data from 2016 [S09].
- Data from interview P06 regarding willingness to pay and struggle with meal decisions is methodologically compromised due to persistent leading interview questions [P06:t1, P06:t9].
