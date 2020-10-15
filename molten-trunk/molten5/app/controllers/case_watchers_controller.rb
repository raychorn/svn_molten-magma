class CaseWatchersController < ProtectedController
  #################
  ### Behaviors ###
  #################
  helper :cases
  
  ###############
  ### Filters ###
  ###############
  before_filter :set_account, :only => %w(account update_subscriptions_from_account)
  before_filter :set_case, :only => %w(case update_subscriptions_from_case)
  before_filter :can_view_account, :only => %w(account)
  before_filter :can_view_case, :only => %w(case)
  
  ###############
  ### Actions ###
  ###############
  
  ### Read Actions ###
  
  # Returns contacts associated with the account (params[:from_account]) case watcher. 
  def account
    # find the account we are grabing contacts from
    if id = params[:from_account]
      @selected_account = Sfaccount.find(id)
    end
    # super users can only add themselves.
    if current_contact.portal_privilege == AppConstants::PRIVILEGE[:super_user]
                  @instruction_text = "Your current access level is \"Super User\" and you can only subscribe 1 contact: yourself."
                  @contacts = [current_contact]
                else
                  @contacts = (@selected_account || @account).contacts.find(:all, :order => 'last_name', :conditions => ["email NOT IN (?) and email IS NOT NULL and email != ''",['null@null.null','no@no.no']])
                  if current_contact.portal_privilege == AppConstants::PRIVILEGE[:user_manager]
                    @instruction_text = "Your current access level is \"User Manager\" and you can subscribe other contacts from your company."
                  end
                end
    # the current subscribers
    @subscribers = @account.watcher ? @account.watcher.contacts : []
    # set siblings if (a) this account can view child accounts and (b) it has sibling accounts
    @siblings = ((@account.portal_case_scope__c == Sfaccount::SCOPES[:children_accounts] and @account.sibling_accounts) ? @account.sibling_accounts.reject { |a| a.contacts(true).empty? } : [])
    
  end
  
  # Returns contacts associated the the support case's case watcher.  
  def case
    @account = @case.account
    # find the account we are grabing contacts from. this is used in the pulldown selection menu.
    if id = params[:from_account]
      @selected_account = Sfaccount.find(id)
    end
    # super users can only add themselves.
    if current_contact.portal_privilege == AppConstants::PRIVILEGE[:super_user]
                  @instruction_text = "Your current access level is \"Super User\" and you can only subscribe 1 contact: yourself."
                  @contacts = [current_contact]
                else
                  @contacts = (@selected_account || @account).contacts
                  if current_contact.portal_privilege == AppConstants::PRIVILEGE[:user_manager]
                    @instruction_text = "Your current access level is \"User Manager\" and you can subscribe other contacts from your company."
                  end
                end
    @subscribers = @case.watcher ? @case.watcher.contacts : []
    # set siblings if (a) this account can view child accounts and (b) it has sibling accounts
    @siblings = (@account.portal_case_scope__c == Sfaccount::SCOPES[:children_accounts] and @account.sibling_accounts) ? @account.sibling_accounts.reject { |a| a.contacts(true).empty? } : []
  end
  
  ### Update Actions ###
  
  # Updates subscriptions for an account, subscribing and unsubscribing contacts.
  def update_subscriptions_from_account  
    contacts = params[:contacts]
    contacts_subscribing = params[:subscribers].is_a?(Hash) ? params[:subscribers].keys : []
    contacts_unsubscribing = params[:contacts] - contacts_subscribing
    
    # subscribe these contacts
    contacts_subscribing.each do |c_id|
      begin
        Case_Watcher.create_subscription!(Contact.find(c_id), 
                                        :account => Sfaccount.find(params[:id]).synced_record )
      rescue  ActiveRecord::RecordNotFound
        logger.info("Couldn't create subscription for contact w/id: #{c_id}. Contact doesn't exist.")
      end
    end

    # unsubscribe these contacts
    contacts_unsubscribing.each do |c_id|
      begin
        Case_Watcher.remove_subscription!(Contact.find(c_id), 
                                        :account => Sfaccount.find(params[:id]).synced_record )
      rescue  ActiveRecord::RecordNotFound
        logger.info("Couldn't remove subscription for contact w/id: #{c_id}. Contact doesn't exist.")
      end
    end
    
    redirect_to :action => 'account', :id => @account, :notice => "Account subscriptions updated."
  end
  
  # Updates subscriptions for a case, subscribing and unsubscribing contacts.
  def update_subscriptions_from_case
    contacts = params[:contacts]
    contacts_subscribing = params[:subscribers].is_a?(Hash) ? params[:subscribers].keys : []
    contacts_unsubscribing = params[:contacts] - contacts_subscribing
    
    logger.info "Found #{contacts_subscribing.size} subscribing"
    logger.info "Found #{contacts_unsubscribing.size} unsubscribing"
    
    # subscribe these contacts
    contacts_subscribing.each do |c_id|
      begin
        Case_Watcher.create_subscription!(Contact.find(c_id), 
                                        :support_case => Sfcase.find(params[:id]).synced_record )
      rescue  ActiveRecord::RecordNotFound
        logger.info("Couldn't remove subscription for contact w/id: #{c_id}. Contact doesn't exist.")
      end
    end
    if contacts_unsubscribing.any?
      logger.info("[CASE WATCHER] Removing subscription for: #{contacts_unsubscribing.join(',')}")
    end
    # unsubscribe these contacts
    contacts_unsubscribing.each do |c_id|
      begin
        Case_Watcher.remove_subscription!(Contact.find(c_id), 
                                        :support_case => Sfcase.find(params[:id]).synced_record )
      rescue  ActiveRecord::RecordNotFound
        logger.info("Couldn't remove subscription for contact w/id: #{c_id}. Contact doesn't exist.")
      end
    end
    redirect_to :action => 'case', :id => @case, :notice => "CR subscriptions updated."
  end
  
  # Updates the current contact's account subscriptions
  def update_contact_account_subscriptions
    accounts = params[:accounts]
    accounts_subscribing = params[:account_subscriptions].is_a?(Hash) ? params[:account_subscriptions].keys : []
    accounts_unsubscribing = accounts - accounts_subscribing
    accounts_unsubscribing.each do |a_id|
      Case_Watcher.remove_subscription!(current_contact.synced_record, 
                                        :account => Sfaccount.find(a_id).synced_record )
    end
    redirect_to :controller => 'contact', :action => 'settings', 
                :notice => "Account subscriptions updated."
  end
  
  # Updates the current contact's case subscriptions
  def update_contact_case_subscriptions
    cases = params[:cases]
    cases_subscribing = params[:case_subscriptions].is_a?(Hash) ? params[:case_subscriptions].keys : []
    cases_unsubscribing = cases - cases_subscribing

    cases_unsubscribing.each do |c_id|
      Case_Watcher.remove_subscription!(current_contact.synced_record, 
                                        :support_case => Sfcase.find(c_id).synced_record )
    end
    redirect_to :controller => 'contact', :action => 'settings', 
                :notice => "Cases subscriptions updated."
  end
  
  # Subscribes the +current_contact+ to either an account or support case depending on the 
  # params. See +#set_options+ for how this is done.
  def subscribe
    Case_Watcher.create_subscription!(current_contact.synced_record, set_options )
    if request.xhr?
      render :update do |page|
        page.alert "Case Watcher Created."
        page.replace_html "subscribe_container", set_subscribe_link
      end
    else
      flash[:notice] = "Case Watcher Created."
      redirect_to(:back)
    end
    
  end
  
  def unsubscribe
    Case_Watcher.remove_subscription!(current_contact.synced_record, set_options )
    if request.xhr?
      render :update do |page|
        page.alert "Case Watcher Removed."
        page.replace_html "subscribe_container", set_subscribe_link(options = {:subscribe => true})
      end
    else
      flash[:warning] = "Case Watcher Removed."
      redirect_to(:back)
    end
  end
  
  private
  
  def set_account
    @account = Sfaccount.find(params[:id])
  end
  
  def set_case
    @case = Sfcase.find(params[:id])
  end
  
  # If an +account+ instance variable is set, the
  # +current_contact+ must be able to share cases for that account.
  def can_view_account
    if @account
      if !current_contact.share_cases?(@account)
        render :text => "You are not authorized to view this account."
        return true
      end
    end
  end
  
  # If a +case+ instance variable is set, the
  # +current_contact+ must be able to view this case.
  def can_view_case
    if @case
      if !current_contact.share_cases?(@case.account)
        render :text => "You are not authorized to view this case."
        return true
      end
    end
  end
  
  # Used in the +#subscribe+ and +#unsubscribe+ actions to remove/add a contact
  # to a case watcher.
  def set_options
    options = if params[:account]
                  {:account => Sfaccount.find(params[:account]).synced_record}
              elsif params[:support_case]
                  {:support_case => Sfcase.find(params[:support_case]).synced_record}
              end
  end
end
