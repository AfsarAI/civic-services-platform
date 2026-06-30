# User Manual

This folder contains end-user documentation for the Civic Services Platform.

## Roles

The platform has exactly **3 user roles** (per Milestone 1 Report):

### Citizen
- Register an account and log in
- Submit a complaint (report a pothole with photo and location)
- Track the status of submitted complaints in real time
- Edit or cancel a complaint (only while status is `pending` and not yet assigned)
- Provide feedback and a rating after a complaint is resolved
- View full complaint history

### Administrator *(consolidated role)*
Covers municipal administration, senior management, and system administration.
- Log in with admin credentials
- View all submitted complaints (filterable by status, priority)
- Prioritize complaints (low / medium / high / critical)
- Assign complaints to field workers
- Monitor complaint progress across all assignments
- Verify completed repairs and close complaints
- Generate reports and view analytics / performance metrics
- Manage user accounts (create, activate, deactivate)
- Assign roles and control platform access

### Field Worker
- Log in with field worker credentials
- View all complaints assigned to them
- Accept an assigned complaint
- Update repair progress (`in_progress`)
- Mark a complaint as complete and upload photographic evidence
- View work history

## Complaint Lifecycle

```
pending  →  assigned  →  in_progress  →  resolved  →  closed
   ↑ citizen submits   ↑ admin assigns  ↑ FW updates   ↑ FW completes  ↑ admin verifies & closes
```

- Citizen can **edit** or **cancel** only while status = `pending`
- Field worker moves status: `assigned` → `in_progress` → `resolved` (with evidence upload)
- Administrator verifies resolved complaints and moves to `closed`
- Administrator can `reject` a complaint at any stage

## TODO

- [ ] Add step-by-step user guides with screenshots
- [ ] Add FAQ section
- [ ] Add video walkthroughs
