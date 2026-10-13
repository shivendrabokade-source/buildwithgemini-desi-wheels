# My agent: DesiWheels

One-liner: A conversational advisory and matchmaking agent that helps Indian car buyers find verified used cars, navigate local market rules, calculate real ownership costs, and avoid common used-car scams.

Tool coverage:
- Memory: Remembers buyer profile across sessions: budget range (in ₹ Lakhs), home city/RTO state (e.g., Delhi NCR, Bengaluru, Mumbai), preferred fuel type (Petrol, Diesel, CNG, EV), transmission preference (MT/AT), family size, and shortlisted cars.
- Tools: 
  - `search_cars`: Queries catalog filtered by budget, city, make, model, year, and fuel type.
  - `check_rto_compliance`: Checks local regulations (e.g., NGT 10-yr diesel / 15-yr petrol rule in Delhi-NCR, BS4 vs BS6 compliance, interstate NOC transfer taxes).
  - `fair_price_estimator`: Benchmarks fair market value based on age, odometer reading, owner count, and depreciation.
  - `scam_and_inspection_checklist`: Generates tailored inspection checklists (accidental meter tampering, flood damage signs, service history verification, RC hypothecation status).
- Catalog/UI: Collection of car listings with photos, specs, pricing (₹ Lakhs), and condition tags rendered as A2UI comparison cards and specs tables.
- Image gen: Generates visuals of customized vehicles, car lifestyle scenarios (e.g., road-tripping in the Western Ghats or Himalayas), or visual inspection callout references.
- Sandbox: Performs financial computations: customized EMI schedules (loan tenure, interest rate, down payment in INR) and 3-to-5 year total cost of ownership (TCO) comparing petrol vs diesel vs EV running costs.

Recommended for every project: memory, storage, tools, image generation, A2UI
Agent-specific / stretch (pick what fits): code sandbox for EMI/TCO financial calculations, live RTO/fuel price lookups, Cloud Trace for latency tracking.
