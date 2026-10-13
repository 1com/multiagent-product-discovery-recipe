# PantryPal discovery brief

## 1. Recommendation
We recommend testing further before writing code [UNSUPPORTED]. The target problem of daily dinner decision fatigue and preventable food waste is genuine across multi-person households [P01:t2, P02:t2, P03:t2, P04:t2, idea_brief]. However, participants explicitly reject manually inventorying their pantry, and rigid automated planning causes abandonment [P02:t8, P05:t4, P05:t8]. We must run low-cost tests on lightweight inventory capture and flexible planning before building a full product [UNSUPPORTED].

## 2. Who the users are
The idea brief targets households of two or more people who cook at home on most weeknights [idea_brief]. The research includes ten interviewees, but only seven represent valid target customer interviews [P01, P02, P03, P04, P05, P08, P10]. P06 was subjected entirely to leading questions, making the interview methodologically invalid [P06:t1, P06:t2, P06:t8]. P07 is a solo university student who cooks once a week and relies on takeout, outside the target definition [P07, P07:t1]. P09 represents a retired couple who have maintained the same cooking routine for forty years with zero desire for digital tools [P09, P09:t1].

The valid users fall into three core segments [UNSUPPORTED]:
- Busy working families with children who juggle irregular schedules and picky eaters [P01, P04].
- Dual-income working couples with late hours and uncoordinated grocery shopping [P02, P08].
- Shared flatmates managing joint ingredients in a shared kitchen [P10].

## 3. Problems that are real
- Decision fatigue and mental load: Daily deliberation over what to cook causes chronic stress [P01:t2, P03:t2, P04:t2, P05:t2]. Adults spend 22 minutes each day deciding what to cook [S04]. One parent reported, "It's the mental load. Every single day somebody has to decide what's for dinner, and that somebody is me." [P01:t2]. Another described, "Around four in the afternoon the 'what do we eat tonight' dread starts." [P05:t2].
- Accidental food waste and duplicate shopping: Uncoordinated household members frequently buy identical items while existing food rots [P02:t2, P02:t4, P04:t4, P10:t2]. A participant observed, "We bought basil twice in one week because each of us thought we were out. Both went bad." [P02:t4]. Another reported that their spouse bought chicken while they also bought chicken that same afternoon, overloading the freezer [P04:t4]. European households discard 19% of the food they buy [S01], with an average weekly grocery spend of EUR 118 for a two-person household [S02].
- Lack of weeknight time and rigid plan failure: Dinners must take 30 minutes or less on weeknights [P01:t1, P01:t8, P04:t8]. Static weekly plans collapse when schedules shift, resulting in guilt and app abandonment [P03:t4, P05:t1, P05:t4]. One user noted, "I tried a meal-planning app once. By Thursday I hadn't followed the plan and I just stopped opening it." [P05:t4].

## 4. What the evidence says
Across eight usable transcripts (excluding P06 for leading questions and P07 as out of scope), the evidence reveals clear behavioral patterns alongside stated preferences [P01, P02, P03, P04, P05, P08, P09, P10]:
- Behavioral evidence: Real dinner execution is dominated by quick fallbacks, such as cooking fish fingers, toast, or ordering takeout when planning fails [P01:t3, P02:t3, P05:t3]. Households currently rely on shared list apps, notes apps, paper pads on fridges, or online repeat orders, but lists do not connect to inventory [P01:t5, P01:t6, P02:t6, P03:t6, P04:t6, P10:t6]. Only 11% of households currently use a meal-planning app [S03].
- Friction with manual inventory: Four separate participants stated identical concerns regarding logging food: "Setup has to be fast. If I need to type in my whole pantry I'll quit on day two." [P02:t8, P05:t8, P08:t8, P10:t8].
- Desire for control: Multiple participants stated that they refuse automated rigidity, demanding: "I want to edit the plan easily. I don't want an app dictating to me." [P01:t8, P02:t8, P03:t8, P05:t8]. One participant stated, "Planning is my favourite part of the week, honestly. I would never want an app to take that away from me." [P03:t1]. Another stated, "Planning ahead stresses me out. A plan I don't follow feels like failure, so I decide on the day." [P05:t1].
- Pricing evidence: Willingness to pay is tightly constrained [P01:t9, P02:t9, P03:t9, P05:t9]. Median stated willingness to pay for a cooking app across the market is EUR 3.50 per month [S05]. Participants indicated they would pay a few euros only if it demonstrably cut grocery waste [P01:t9, P02:t9, P10:t9]. P08 claimed an extreme willingness to pay EUR 30 a month after throwing out EUR 200 of spoiled holiday food, but this represents an unvalidated extreme stated preference following a one-off trauma [P08:t2, P08:t9].

## 5. Competitors and market
The market includes multiple existing solutions, none of which fully unify pantry inventory, adaptive planning, and household collaboration [C:FridgeChef, C:MealLoop, C:PlanPlate, C:PantryGenie, C:WeekWise, C:ZeroWaste Kitchen, C:SupperSync]:
- Photo recipe tools: FridgeChef offers recipe suggestions from photos of your fridge at EUR 4.99 per month or free with ads, targeting improvising individuals rather than families [C:FridgeChef].
- Meal planners: MealLoop targets families with weekly plans, grocery lists, and family sharing at EUR 6.99 per month or EUR 49.99 per year, but does not track existing pantry stock [C:MealLoop]. PlanPlate offers calendar-based meal planning at EUR 2.99 per month for couples and flatmates [C:PlanPlate]. WeekWise targets budget families with store comparisons and plans for free or EUR 29.99 one-off [C:WeekWise].
- Inventory trackers: PantryGenie tracks inventory using barcode scanning and expiry alerts at EUR 3.99 per month, but lacks dynamic recipe planning [C:PantryGenie]. ZeroWaste Kitchen provides leftover recipes supported by donations [C:ZeroWaste Kitchen].
- Shared household tools: SupperSync provides dinner planning, a who-cooks rota, and shared lists for EUR 4.49 per month per household [C:SupperSync].

## 6. Risks and open assumptions
- Inventory onboarding friction risk: If users are forced to scan or type pantry contents manually, they will churn immediately [P02:t8, P05:t8, P08:t8, P10:t8].
- Rigid plan abandonment risk: If plans cannot instantly adapt when work or family schedules change, users feel like failures and abandon the tool [P01:t8, P05:t1, P05:t4].
- Household sync risk: Uncoordinated shopping by multiple partners creates waste and duplicates unless updates sync in real time [P02:t2, P04:t4, P10:t2].
- Monetization viability risk: At a median willingness to pay of EUR 3.50 per month, subscription revenue will be thin, and price points above EUR 5 face heavy resistance [P02:t9, S05].

## 7. What to test next
- Experiment 1 (Pantry capture concierge test): Test whether busy households will log pantry items via receipt photo or grocery order forward rather than manual entry [UNSUPPORTED]. Metric: At least 60% of test households submit their weekly receipt over 3 consecutive weeks, tested across 30 households [UNSUPPORTED].
- Experiment 2 (Flexible planning landing page smoke test): Run ads pitching flexible dinner plans editable in 30 seconds rather than static full-week plans [UNSUPPORTED]. Metric: A conversion rate of over 8% email signups from 500 landing page visits [UNSUPPORTED].
- Experiment 3 (Willingness-to-pay pre-order test): Test paywall conversion at EUR 2.99 versus EUR 4.99 per month on a clickable prototype [UNSUPPORTED]. Metric: A minimum 5% paid pre-order conversion rate on a sample of 200 qualified leads [UNSUPPORTED].

## 8. Unsupported or weak claims
- Claim that 97% of households would pay for automated meal planning: This figure from App Trends Blog is an extreme outlier contradicted by interview data where most users seek free or low-cost apps [P01:t9, P02:t9, P03:t9, P05:t9, S08].
- Claim that the meal-planning market grows by 25% annually: Snippet S06 lists no source and no year, making it unverified [S06].
- Claim that 73% of families struggle with dinner decisions: Snippet S07 provides no source and no year, making it unverified [S07].
- Claim that online grocery purchases represent only 4%: Snippet S09 comes from a 2016 study, which is a decade old and likely outdated [S09].
- P06 interview data: All statements in interview P06 are invalid due to aggressive leading questions by the interviewer [P06:t1, P06:t2, P06:t3, P06:t4, P06:t5, P06:t6, P06:t7, P06:t8, P06:t9].
