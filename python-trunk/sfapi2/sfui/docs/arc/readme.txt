
Overview of the "CR to Fix" Process supported by SalesForce
                                                              Sept 8th, 2004 

This is our third release of a customization of SalesForce to
support the Magma "Branch Approval" or "CR to Fix" process.  This
version eliminates the usage of the MOD object and brings a number
of very helpful features.  This file gives you an overview of
the new structures in SalesForce and changes to the scripts 
available on all Magma linux machines.

A Task Branch is a SalesForce object which ties together  one or more CRs
a branch, and a Code Stream. A Task Branch documents which CRs are being 
addressed in a specific Code Stream by the indicated Branch. A number of 
lists are available on the Task Branch page to provide one-click access 
to related CRs, Team Branches, and approvers.  Much of the same information 
is also available from command prompt scripts and email alert messages.


Task Branch Structure:
  Header: 
    - Task Branch label & code stream.
    - Priority and risk with details of this risk.
    - Merge date and build path updated after SCM merge & build.
    - System dates and ClearCase branch path
    
  Branch Approvals:
    - Each Branch Approval addresses a different aspect of the approval process.
        - Developer -> Eng Mgr -> PE -> SCM -> CR Testing -> CR Closed
    Each Task Branch has 5 or more Branch Approvals as below:
    - Developer alias link & timestamp when fix submitted for approval.
    - Engineering Manager alias link & timestamp of approval.
    - Product Engineer alias link & timestamp of approval.
    - (Optional) Team Manager alias link & timestamp of approval.
    - SCM status & timestamp of status change.
       Received -> QOR -> Bundle -> Approve -> Patch Build
    - Series of CR Originator alias links & timestamp of fix acceptance.
    
  Related CRs:
    - Link to the CRs being addressed by this Task Branch.
    - Status of this CR (updated as Task Branch changes).  
       (Note: CR status is a combination of required Task Branch statuses)
    - Link to the product component this CR addresses (components define PE)
       
  Team Branches: (Optional)
    - Links to the Team Branches that manage this Task Branch through SCM.
      (Skip to the "Team Branch Overview" to understand Team vs. Task Branches)
      
  Notes & Attachments:
    - Branch Details is a note created from the comments in the related MODs.
    - Other notes and attachments can be added by anyone interested.
    
  Mod Migrations:
    - Link to the MODs that represented this Branch in SalesForce.
      (The MODs will all be deleted after migration is complete)
      

Change to CR View:
  Related Task Branches:
    List of Task Branches with fixes that address this CR.
    - Code Stream targeted for this Task branch.
    - Link to Task Branch page with branch name.
    - Task Branch status (updated on Branch change)
    - Link to product Component for this CR.
    
    
    
New SalesForce header Tabs. (use far right arrow to change tab order)

  Branch Approvals Tab:
    Branch Approvals replace much of the approval functionality provided by MODs.
    Engineering managers and PE can use this Tab to have quick access to BAs.
    - "All my Approvals" view shows Branch Approvals owned by you.    
    - "My Approvals Needed" view shows Branch Approvals needing your approval.
    - "View All - Eng Manager - Need Approval" view shows all Manager Approvals.
    - "View All - Pro Engineer - Needs Approval" view shows all PE Approvals

  Task Branches Tab:
    The Task Branch tab allows you to quickly see Task Branches owned by you.
    (Task Branches are owned by the Developer who created the ClearCase branch)
    - "My Task Branches" view shows Task Branches owned by you. 
    
  Team Branches Tab:
    The Team Branch tab allows you to quickly see Team Branches owned by you.
    (Team Branches are owned by the Team Manager of each Team)
    - "My Team Branches" view shows Team Branches owned by you. 
    
    
Process Flow:  (command line script noted in "[]" brackets)

CR Originator View:
  
  CR created     Assigned     Review CR      Notified       Close CR
    with     ->  to queue  -> for status  -> SCM merged  -> tested
  component                    changes       test build     pass/fail

Developer View:
  
  Accept CR      Create       Link CR     Fix       Submit      Monitor
  from queue ->  CearCase  -> to Task ->  Issue  -> Branch  ->  SCM merge
  or mgr         Branch       Branch      & test                conflict
                              [lncr]             [submitbranch]

Engineering Manager View:

  Ensure CR     Notified      Check for      Approve     Monitor Developer
  accepted  ->  Developer  -> linkage to  -> Branch  ->  SCM merge conflict
  by team       branch fix    Team Branch    Fix         response time
                                         [approvebranch]
  
Product Engineer View:

  Notified      Check if required     Validate     Approve
  Eng Mgr.  ->  to link with open  -> Branch    -> Branch
  Approved      Team Branch           Fix          Fix
                                                  [approvebranch]
  
SCM View:
 
  Receive       Accept Branch       QOR       Bundle     Patch    Notify
  token in  ->  into team       -> Testing -> Testing -> Build -> Build
  dropbox       (ps, fe, be, an)                                  Available
  


Command Line scripts:
  All scripts are available from the global path "/home/sfscript/sfui". 
  Add this to your PATH environment variable or prepend to each script 
  call.  On first use of any script you will be asked for your SaleForce
  login username/password.
  Usage information for all scripts is available using the script "task"
  for basic Task Branch scripts and "team" for Team Branch specific.
  
  ~ task          - shows basic usage information for all scripts below.
  ~ lncr          - used by developer to link a CR to a branch (also addmod).
  ~ unlinkcr      - used by developer to unlink a CR to a branch (also rmmod).
  ~ submitbranch  - used by developer to submit branch for approval.
  ~ approvebranch - used by manager and PE to approval branch.
  ~ lsbr          - used by all to get status of the Task Branch.
  ~ lsbrs         - used by all to get status of Task branches for a user alias
  
  Team Branch Oriented script.
  ~ teamlnbranch  - used by all to link a Task Branch to a Team Branch
  ~ teamsethold   - used by Team manager to disable linking to Task Branches
  ~ teamsettest   - used by Team manager to indicate Team Branch in test mode
  ~ teamapprovebranch - used by Team manager to submit Team Branch to SCM
  ~ teamls        - used by all to list Task Branches in Team Branch.
  

Cron Jobs:
  A number of cron jobs are used to activate the workflows in this process
  and syncronize information between SCM and SalesForce.  If you feel a
  Task Branch is stuck please email "Salesforce-support@molten-magma.com" with
  the branch name and we will address the issue.
  
  - walkSF  - Scans SalesForce continuously for Task/Team & Approval changes
  - walkSCM - Scans token file every 15 min. and updates Task/Team status.
  
  
Task Branches::

Task Branch States (Typical Process) 
  The following table lists the most common states and provides a brief 
  description of each. 

  - Fixing               - Branch is still in development 
  - Approving by Manager - Submitted for approval to the engineering manager. 
  - Approving by PE      - Submitted for approval to the Product Engineering.
  - Submitted to SCM     - Submitted to SCM, but not accepted yet.
  - SCM-Received         - Accepted by SCM but the merge process not begun.
  - SCM-QOR Building     - Build created to verify Quality of Results 
  - SCM-QOR Testing      - The QOR build is currently running the QOR tests. 
  - SCM-QOR Results      - The QOR Tests results are being evaluated.
  - SCM-Ready to Bundle  - The QOR Tests were acceptable. 
  - SCM-Bundle Building  - Bundle of Branches is being assembled.
  - SCM-Bundle Testing   - Build for this Branch’s Bundle is being Tested.
  - SCM-Bundle Results   - Results for this Bundle are being evaluated. 
  - SCM-Approved         - Build is acceptable for a Patch Build, but not started. 
  - SCM-Hold             - Hold requiring action from a developer.
  - SCM-Patch-Building      - Patch build with this branch is in progress.
  - SCM-Patch-Build Testing - Patch build candidate is being tested.
  - SCM-Patch-Build Results - Patch build results are being reviewed. 
  - Merged – Testing by Originator - Patch build has been released with a CR fix. 
     (The CR originator is expected to test the fix and disposition the CR.) 

Team Branches::
  Developers may also link there Branches together in something called
  a Team Branch. A Team Branch allow a specific development team to do
  trial merges and integration testing before submitting there code
  changes to SCM.  


Team Branch States 
  Several Additional States are used by Team Branches. Team branches are 
  bundled together before being submitted to SCM by a member of the 
  development team. 

  - Awaiting Branches  - Team Branch is open for linkage to Task Branches
  - Team Hold          - Team Branch is closed to new Task Branch links.
  - Team Build Testing - Team Branch in active bundle testing by Team.
  - Team Approved      - Team Branch passed team test, submitted to SCM.


General Overview of the "CR to Fix" Process supported by SalesForce

Magma generally maintains three active code streams at any one time - two 
that are released to the field and a third which becomes the next release. 
At the time of this writing, they are 4.1, 4 and the "next" release which 
is called blast 5. Any given CR may be fixed in one or more code streams, 
depending on the nature of the need, the resources available, and state 
of the release for the code stream. 

A field called "Code Streams & Priority" in the top section of each CR 
specifies which codes streams will be addressed for a given CR. The code 
streams are listed by order of priority. If the code stream is not listed 
in this field, a fix for that code stream is not expected. Once a branch 
is completed and tested for each of these code streams the CR may be closed.

Developers create their code changes in something called a Task Branch, 
managed by a tool called ClearCase. Branches may contain changes for a 
single CR or several CRs. The SCM team is responsible for producing builds 
by merging branches into the active code streams. Often branches are 
grouped together into a Bundle to facilitate the process.

Developers may also link there Branches together in something called
a Team Branch. A Team Branch allow a specific development team to do
trial merges and integration testing before submitting there code
changes to SCM.  

Periodically, a new build is produced for each code stream that contains 
multiple branches. These builds are called "Patch Builds" to indicate 
minimal testing that has gone into them. They are not typically available 
for general release, but are available for internal testing of the CRs 
they address. See the How To article entitled "How to find a red build 
which fixes my CR" for information where these builds can be found. 

The object which ties together a CR, a Branch, and a Code Stream is called
a Task Branch. A Task Branch documents that one or more CRs are being 
addressed in a specific Code Stream by the indicated Branch. A number of 
lists are also available in the Task Branch to provide from within 
SalesForce one-click access to related CRs, Team Branches, and approvers.  
Much of the same information is also available from command prompt scripts 
and email alert messages explained below.

If you have further question please check the FAQ.txt file and check the
solutions we have created in SalesForce https://na1.salesforce.com/501/o
If you do not find an appropriate solution then please contact us at
salesforce-support@molten-magma.com.  