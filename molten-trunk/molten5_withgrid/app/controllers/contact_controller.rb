class ContactController < ApplicationController
  authorize :actions => [:settings]
  
  def login_form
    render :layout => 'blank'
  end
  
  def forgot_password
    render :layout => 'blank'
  end
  
  def retrieve_password
      if params[:email].nil?
          flash[:warning] = "Please provde an email address."
      else
          contact = Sfcontact.find_by_email(params[:email])
          if contact and contact.contact_status__c != 'Active'
            flash[:warning] = "Your account has been disabled. Please contact molten_feedback@molten-magma.com for support."
          elsif contact and Sfcontact.forgot_password(params[:email],request.port_string,request.host)
            flash[:notice] = "Instructions on retrieving your password have been sent to #{contact.email}"
          else
            flash[:warning] = "We couldn't find a user account with the email address: #{params[:email]}"
          end
      end   
      render :action => 'forgot_password', :layout => 'blank'
  end
  
  def settings
    set_contact_vars
  end
  
  def update
    @contact = current_contact
    if @contact.update_attributes_and_sync(params[:contact])
      flash[:notice] = "Settings Updated."      
    end
    set_contact_vars
    render(:action => 'settings')
  end
  
  def status
    if params[:email].blank?
      flash[:warning] = "Please provide an email address."
      return redirect_to(:action => 'status_form')
    end
    unless @lead_or_contact = Lead.find_by_email(params[:email])
      @lead_or_contact = Contact.find_by_email(params[:email])
    end
     if @lead_or_contact.nil?
       flash[:warning] = "No registration information found for #{params[:email]}"
       return redirect_to(:action => 'status_form', :email => params[:email])
     end
  end
  
  def send_lead_reminder
    @lead = Lead.find_by_id(params[:id])
    SfcontactMailer.deliver_lead_reminder(@lead)
    flash[:warning] = "A reminder has been sent to #{@lead.owner.name}"
    redirect_to(:action => 'login_form')
  end
  
  def status_form
  end
  
  def login
    if @contact = Sfcontact.authenticate(params[:email],params[:password],request)
      set_cookies
      set_time_offset
      set_lava_cookies(@contact)
      if @downtime = SfmoltenPost.check_downtime_announcement
         render(:action => 'scheduled_maintenance')
      else
        return redirect_to_stored_or_default(default_url)
      end
    else
      flash[:warning] = "Sign-in failure. Username or Password is incorrect."
      return render(:action => 'login_form',:layout => 'blank')
    end
  end
  
  def login_from_sf
    if @contact = Sfcontact.authenticate_by_id(params[:id])
      set_cookies
      set_lava_cookies(@contact)
      if @downtime = SfmoltenPost.check_downtime_announcement
         render(:action => 'scheduled_maintenance')
      else
        return redirect_to_stored_or_default(default_url)
      end
    else
      flash[:warning] = "Sign-in failure"
      return render(:action => 'login_form',:layout => 'blank')
    end
  end
  
  def confirm
    if params[:id].nil? or params[:token].nil?
      flash[:warning] = "An error occurred processing the confirmation. Please try confirming again."
    elsif @contact = Sfcontact.confirm(params[:id],params[:token])
      cookies[:contact_id] = @contact.id
      return redirect_to(:action => 'settings', :notice => "Your account has been confirmed.")
    else
      flash[:warning] = "Your account cannot be confirmed at this time."
    end
    return render(:layout => 'blank')
  end
  
  def logout
    if current_contact
      session[:contact_id] = nil
      clear_lava_cookies
      clear_cookies
    end
    return redirect_to(url_for(:action => 'login_form'))
  end
  
  def change_password
    @contact = current_contact || (Sfcontact.find_by_id_and_token(params[:id], params[:token]) || Sfcontact.find_by_sf_id_and_portal_password__c(params[:id],nil))
    unless @contact
      flash[:warning] = "We couldn't find the contact to change the password."
      return redirect_to(:controller => 'home', :notice => flash[:warning])
    end
  end
  
  def update_password
    @contact = current_contact || Sfcontact.find_by_id_and_token(params[:id], params[:token]) || Sfcontact.find_by_sf_id_and_portal_password__c(params[:id], nil)
    set_contact_vars
    unless @contact
      flash[:warning] = "We couldn't find the contact to change the password."
      return redirect_to(home_url)
    end
    
    if @contact.change_password!(params[:password], params[:password_confirmation]) and @contact.valid?
      flash[:notice] = "Your password has been changed."
    end
    
    if current_contact
      return render(:action => "settings")   
    else
      if @contact.valid?
      begin
        cookies[:contact_id] = Sfcontact.authenticate(@contact.email,params[:password]).id
      rescue
      end
        return redirect_to(home_url)
      else
        return render(:action => "change_password")
      end
    end
  end
  
  def signup
    Lead.connection.binding.assignment_rule_id = "01Q3000000000vFEAQ"
    
    merged_attributes = {
      :record_type_id => Lead::MOLTEN_REQUEST_RECORD_TYPE,
      :lead_source => 'Molten'
    }
    
    @lead = Lead.new
    if request.post?
      @lead = Lead.new(params[:lead].merge(merged_attributes))
       @lead.validate_attributes = true
       if @lead.save
          LeadMailer.deliver_notification(@lead)  # added by Misha, send email to customer
          return redirect_to(:action => 'signup_confirmation')
       else
          return render(:action => 'signup')
       end
     end
  end
  
  private
  
  def set_contact_vars
     @contact = (current_contact || @contact)
     return unless @contact
     @account_subscriptions = @contact.accounts_subscriptions
     @case_subscriptions = @contact.cases_subscriptions
  end
  
  # These cookies are for authenticating into the File Download Application.
  def set_lava_cookies(contact)
    cookies[:LAVA_Token] = {:value => OpenSSL::HMAC.hexdigest(OpenSSL::Digest::Digest.new(AppConstants::FILE_DOWNLOAD_DIGEST), 
                                                              AppConstants::FILE_DOWNLOAD_KEY, contact.email),
                            :expires => AppConstants::COOKIE_TIME_LIMIT}
  end
  
  # Clears cookies set for file download system. 
  def clear_lava_cookies
    cookies[:LAVA_User] = nil
    cookies[:LAVA_Token] = nil
  end
  
  def set_cookies
    cookies['contact_id'] = { :value => @contact.id.to_s, :expires => AppConstants::COOKIE_TIME_LIMIT } 
    cookies[:token] = { :value => @contact.token, :expires => AppConstants::COOKIE_TIME_LIMIT }
  end
  
  # Takes the current time in milliseconds
  def set_time_offset
    return unless params[:contact_time]
#    contact_time = Time.at(params[:contact_time].to_i / 1000)
#    offset = Time.now - contact_time
    offset = (params[:contact_time].to_i)*60
    cookies[:time_offset] = { :value => offset.to_s, :expires => AppConstants::COOKIE_TIME_LIMIT }
  end
  
  def clear_cookies
    cookies['contact_id'] = nil
    cookies[:token] = nil
  end
end
