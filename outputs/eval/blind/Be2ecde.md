# PantryPal discovery brief

## 1. Recommendation
We recommend to test further before committing engineering resources to build. While dinner decision fatigue and food spoilage are acute pain points across busy households, manual inventory tracking presents severe onboarding and retention friction, and stated willingness to pay is tightly capped around low single digits. We must test low-friction inventory capture and willingness to pay through lightweight prototypes first.

## 2. Who the users are
The target customer defined in the idea brief is households of two or more people who cook at home on most weeknights [idea_brief].

Across the research sample, users fall into distinct segments based on household makeup and cooking behaviour:
- Busy families with children: Working parents managing dense schedules, childcare, and diverse food preferences [P01, P04, P06].
- Multi-adult households without children: Working couples and flatmates navigating uncoordinated shopping, shared kitchen spaces, and irregular work hours [P02, P05, P08, P10].
- Non-target profiles: Solo students who cook infrequently and rely on takeaways, and established retirees with rigid, longstanding cooking routines who do not experience planning friction [P07, P09].

## 3. Problems that are real
- Decision fatigue: Daily cognitive strain from deciding what to cook is widespread across multi-person households [P01:t2, P02:t3, P03:t2, P04:t2, P05:t2]. Adults spend 22 minutes each day deciding what to cook [S04]. One participant noted that around four in the afternoon the dread starts, while another explained that "deciding is exhausting" [P03:t2, P05:t2].
- Food spoilage and financial waste: Unused fresh ingredients regularly expire in the fridge [P01:t2, P01:t4, P02:t2, P02:t4, P03:t2, P05:t2, P08:t2, P10:t2]. Households discard roughly a fifth of the food they buy, specifically 19% [S01]. For example, one participant reported losing twenty or thirty euros a week to waste, and another recounted throwing away roughly two hundred euros of food after a holiday [P03:t2, P08:t2].
- Uncoordinated grocery purchases and duplicate buying: Multiple household members shopping independently causes redundant purchases and spoiled duplicates [P02:t2, P02:t4, P04:t2, P04:t4, P10:t2]. One couple bought basil twice in one week, and another household ended up with duplicate packs of chicken breasts on the same afternoon [P02:t4, P04:t4].

## 4. What the evidence says
Evidence strength is drawn from 10 customer interviews, though interview P06 was heavily compromised by leading questions and provides weak evidence [P06:t1, P06:t2, P06:t3, P06:t4, P06:t5, P06:t6, P06:t7, P06:t8, P06:t9]. Evidence breaks down into observable behaviours, stated preferences, and contradictions:

Behavioural evidence:
- Current coping mechanisms rely on low-friction, unintegrated tools such as notes apps, shared list apps, paper pads on the fridge, and social media recipe screenshots [P01:t6, P02:t6, P03:t6, P04:t6, P08:t6, P10:t6].
- When dinner plans fail, households resort to convenience foods like frozen staples or expensive takeout [P01:t3, P02:t3, P03:t4, P05:t3].
- Abandonment of rigid planning tools is real: one participant abandoned a meal-planning app by Thursday because failing to follow the schedule felt like failure [P05:t1, P05:t4].

Stated preferences:
- Setup friction is an explicit dealbreaker: multiple participants stated verbatim that "if I need to type in my whole pantry I'll quit on day two" [P02:t8, P05:t8, P07:t8, P08:t8, P10:t8].
- Need for plan flexibility: participants demand fast editing and refuse rigid enforcement, stating "I want to edit the plan easily. I don't want an app dictating to me" [P01:t8, P02:t8, P03:t8, P05:t8].
- Realistic constraints: participants require weeknight dinner recipes that take thirty minutes at most [P01:t8, P04:t8].
- Stated willingness to pay: most respondents stated they would only pay a few euros a month (around 3 to 6 euros) or nothing, with only one outlier stating 30 euros [P01:t9, P02:t9, P03:t9, P04:t9, P05:t9, P07:t9, P08:t9, P09:t9, P10:t9].

Contradictions in evidence:
- Spoilage awareness versus fridge inspection: participants express acute guilt regarding wasted food, yet admit they only glance roughly in the fridge before leaving and forget half of what is inside [P02:t5, P08:t5, P10:t5].
- Structured planning versus daily spontaneity: some users plan weekly on Sunday, while others find upfront planning stressful and insist on deciding on the day [P03:t1, P05:t1].

## 5. Competitors and market
Market benchmarks:
- Average weekly grocery spend for a two-person household is EUR 118 [S02].
- Only 11% of households currently use a meal-planning app [S03].
- Median stated willingness to pay for a cooking app is EUR 3.50 per month [S05].

Competitor landscape:
- MealLoop offers weekly plans, grocery lists, diet filters, and family sharing for families at EUR 6.99/month or EUR 49.99/year [C:MealLoop].
- SupperSync targets shared households with shared plans, chore rotas, shared lists, and reminders at EUR 4.49/month per household [C:SupperSync].
- PantryGenie tracks pantry inventory with barcode scanning, expiry alerts, and shopping lists at EUR 3.99/month [C:PantryGenie].
- FridgeChef offers recipe suggestions from fridge photos and ad-free premium at EUR 4.99/month [C:FridgeChef].
- PlanPlate provides simple calendar-based meal planning and shared plans at EUR 2.99/month [C:PlanPlate].
- WeekWise provides budget-oriented meal plans with store price comparison for a EUR 29.99 one-off pack or free tier [C:WeekWise].
- ZeroWaste Kitchen offers free leftover recipes and tips supported by donations [C:ZeroWaste Kitchen].

## 6. Risks and open assumptions
- Onboarding and data maintenance risk: Users strongly reject manual pantry entry; an app requiring extensive upfront or daily manual logging risks immediate drop-off [P02:t8, P05:t8, P10:t8].
- Monetisation risk: The median stated willingness to pay for cooking apps is EUR 3.50 per month, leaving little margin above customer acquisition costs [S05].
- Compliance and rigidity risk: If households miss a planned meal due to schedule changes, rigid plans induce guilt and abandonment [P05:t1, P05:t4].
- Uncoordinated partner adoption: If one partner does not update or consult the app, duplicate purchases continue [P02:t2, P04:t2, P10:t2].

## 7. What to test next
1. Low-friction inventory capture test: Test whether photo capture or receipt scanning successfully captures existing kitchen inventory without manual typing.
- Target sample size: 50 participating households [UNSUPPORTED].
- Success metric: Greater than 70% onboarding completion and inventory accuracy above 85% [UNSUPPORTED].

2. Plan flexibility and adherence concierge test: Deliver a 5-day dinner plan using existing ingredients via WhatsApp, allowing one-click recipe swaps under 30 minutes.
- Target sample size: 30 busy families [UNSUPPORTED].
- Success metric: At least 4 out of 5 planned dinners cooked per household over the week [UNSUPPORTED].

3. Willingness-to-pay landing page test: Test smoke test landing pages offering a weekly pantry-based meal planner at EUR 3.99/month versus EUR 6.99/month.
- Target sample size: 1,000 unique visitors per price variant [UNSUPPORTED].
- Success metric: Checkout click-through rate exceeding 5% at EUR 3.99/month [UNSUPPORTED].

## 8. Unsupported or weak claims
- The claim from an unsourced document that the meal-planning and meal-kit market is growing at 25% annually lacks a verified source and year [S06].
- The claim that 73% of families struggle with dinner decisions is unsourced and has no year [S07].
- The blog claim that 97% of households would pay for automated meal planning directly contradicts interview willingness-to-pay data and median market benchmarks [S05, S08, P05:t9, P07:t9, P09:t9].
- The claim that online grocery share is 4% is outdated data from 2016 and cannot represent current buying habits [S09].
- Interview P06 consists entirely of leading questions confirming the interviewer's biases, making its answers unreliable evidence for customer demand [P06:t1, P06:t2, P06:t3, P06:t4, P06:t5, P06:t6, P06:t7, P06:t8, P06:t9].
