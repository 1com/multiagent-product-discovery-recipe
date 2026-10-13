# PantryPal discovery brief

## 1. Recommendation
We recommend testing further before building [UNSUPPORTED]. While busy multi-person households report significant daily dinner decision fatigue and food waste, manual inventory tracking presents a critical usability barrier [P01:t2, P02:t2, P02:t8]. Willingness to pay is low, clustered around a few euros a month or reliant on free tiers [P01:t9, P02:t9, P03:t9, P05:t9, S05]. We must validate lightweight inventory input and automated planning adoption before committing engineering resources [UNSUPPORTED].

## 2. Who the users are
The target market originally defined comprises households of two or more people cooking at home on most weeknights [idea_brief]. From ten interviews conducted, nine provide usable data, while one interview must be excluded due to pervasive interviewer bias and leading questions [P01, P02, P03, P04, P05, P06:t1, P06:t2, P06:t8, P07, P08, P09, P10].

The most viable segments are:
- Busy families with children: Working parents managing tight weeknight schedules, multiple dietary preferences, and heavy mental load [P01, P04].
- Working couples without children: Dual-income partners who return home late, shop independently without coordination, and default to takeout when planning fails [P02, P08].
- Shared student or young adult flats: Multiple flatmates sharing kitchen storage and duplicate grocery purchases [P10].

Non-viable segments:
- Solo dwellers who cook infrequently and primarily eat out or order food [P07, P07:t1].
- Settled retirees with rigid multi-decade routines who express no interest in digital tools [P09, P09:t1].

## 3. Problems that are real
Three customer problems are strongly grounded in observable behaviour across usable interviews:
- Mental load and decision exhaustion: Deciding what to make every single day causes friction, fatigue, and last-minute defaulting to takeaway or repetitive quick meals [P01:t2, P01:t3, P02:t3, P03:t2, P04:t2, P05:t2, P05:t3]. Adults spend 22 minutes each day deciding what to cook [S04].
- Food waste from forgotten fridge items: Perishable groceries spoil before being used, leading to financial loss and guilt [P01:t2, P01:t4, P02:t2, P03:t2, P05:t2, P08:t2]. Across European households, 19% of purchased food is discarded [S01].
- Uncoordinated shopping and duplicate purchases: Multiple household members buy the same items simultaneously due to disconnected communication, resulting in excess perishables [P02:t2, P02:t4, P04:t2, P04:t4, P10:t2].

## 4. What the evidence says
Evidence strength is assessed across nine unbiased participant transcripts, one compromised transcript, seven competitor profiles, and nine market snippets [P01, P02, P03, P04, P05, P06, P07, P08, P09, P10, C:FridgeChef, C:MealLoop, C:PlanPlate, C:PantryGenie, C:WeekWise, C:ZeroWaste Kitchen, C:SupperSync, S01, S02, S03, S04, S05, S06, S07, S08, S09].

Behavioural evidence:
- Participants actively waste food through poor visibility into their fridges, such as buying basil twice in one week or letting spinach go slimy [P01:t4, P02:t4].
- Busy parents prepare emergency meals such as fish fingers and frozen peas when 6:00 PM arrives without a plan [P01:t3].
- Households resort to shared list apps or paper pads on the fridge, but these tools lack meal-planning intelligence [P01:t6, P02:t6, P03:t6, P04:t6, P09:t6, P10:t6].
- A participant abandoned a previous meal-planning app by Thursday because failing to follow a rigid schedule felt like failure [P05:t4].

Stated preferences:
- Setup friction is an immediate deal-breaker, with multiple participants explicitly warning: "If I need to type in my whole pantry I'll quit on day two" [P02:t8, P05:t8, P07:t8, P08:t8, P10:t8].
- Users demand agency over their meals and insist: "I want to edit the plan easily. I don't want an app dictating to me" [P01:t8, P02:t8, P03:t8, P05:t8].
- Dinner recipes must be realistic for weeknights, requiring 30 minutes at most [P01:t8, P04:t8].

Contradictions in evidence:
- While P03 states "Planning is my favourite part of the week, honestly", she simultaneously states "Deciding is exhausting" [P03:t1, P03:t2].
- P08 expresses willingness to pay 30 euros a month after an extreme holiday spoilage incident, whereas typical users and market studies indicate willingness to pay is only a few euros a month [P01:t9, P02:t9, P04:t9, P08:t9, S05].

## 5. Competitors and market
The digital meal-planning space has an 11% household adoption rate [S03]. A two-person household spends EUR 118 weekly on groceries [S02].

Existing competitors address isolated slices of the workflow:
- C:MealLoop offers weekly plans, grocery lists, diet filters, and family sharing at EUR 6.99/month or EUR 49.99/year for families [C:MealLoop].
- C:PantryGenie provides barcode scanning, expiry alerts, and shopping lists at EUR 3.99/month to reduce waste [C:PantryGenie].
- C:FridgeChef provides recipe suggestions from fridge photos with a free ad-supported tier and premium at EUR 4.99/month [C:FridgeChef].
- C:PlanPlate offers a calendar with shared plans for couples and flatmates at EUR 2.99/month [C:PlanPlate].
- C:SupperSync coordinates household dinner planning and cooking rotas at EUR 4.49/month [C:SupperSync].
- C:WeekWise offers budget meal plans with a free tier and a EUR 29.99 one-off pack [C:WeekWise].
- C:ZeroWaste Kitchen provides leftover recipes supported by donations [C:ZeroWaste Kitchen].

No competitor currently bridges friction-free pantry tracking with flexible dinner planning [UNSUPPORTED].

## 6. Risks and open assumptions
- Friction risk: Users will abandon the app immediately if onboarding or ongoing inventory maintenance requires manual typing [P02:t8, P05:t8, P08:t8, P10:t8].
- Rigidity risk: Strict weekly schedules break down when schedules shift, creating user guilt and churn [P05:t1, P05:t4].
- Monetisation risk: Stated median willingness to pay for cooking apps is only EUR 3.50 per month, leaving little margin for customer acquisition costs [S05].
- Coordination assumption: It remains unproven whether multiple household members will reliably check or update a shared inventory app [UNSUPPORTED].

## 7. What to test next
- Test 1: Onboarding and receipt scan concierge test. Test whether users will photograph a grocery receipt to populate their pantry rather than typing items [UNSUPPORTED]. Target 60% completion rate across 50 recruited households [UNSUPPORTED].
- Test 2: Flexible meal plan adoption prototype. Offer dynamic 30-minute recipes based on on-hand ingredients with an edit-plan feature [UNSUPPORTED]. Measure whether households cook at least 3 suggested meals in a 7-day period with a target of 50% across 40 households [UNSUPPORTED].
- Test 3: Shared household duplicate prevention test. Deploy a shared pantry and shopping sync between partners [UNSUPPORTED]. Measure whether duplicate purchases decrease by 75% over two weeks across 30 couples [UNSUPPORTED].
- Test 4: Pricing smoke test. Run landing page ads testing EUR 2.99/month versus EUR 4.99/month value propositions [UNSUPPORTED]. Target a 5% pre-order click-through conversion rate on 1,000 visitors per variant [UNSUPPORTED].

## 8. Unsupported or weak claims
- The claim that 97% of households would pay for automated meal planning originates from an unverified blog and is contradicted by interview willingness to pay data [P01:t9, P02:t9, P05:t9, P07:t9, P09:t9, S08].
- The claim of 25% annual growth in the meal-planning market lacks an identified research source or publication year [S06].
- The statistic that 73% of families struggle with dinner decisions has no source or year attached [S07].
- The data point stating 4% of grocery purchases occur online dates from 2016 and is outdated [S09].
- The entire interview P06 is compromised due to interviewer bias, containing leading questions that presupposed stress, nightmare scenarios, and willingness to pay [P06:t1, P06:t2, P06:t3, P06:t4, P06:t5, P06:t6, P06:t7, P06:t8, P06:t9].
