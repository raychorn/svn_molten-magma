class Admin::ContactsController < AbstractAdminController

  # Contacts browse and search action. This is the default page for the 
  # admin area. 
  # 
  # By default, returns a list of all contacts the +current_contact+
  # has access to. 
  # 
  # Optional params:
  # - company_id => Restricts the list of contacts to the 
  #                 specified company. 
  # - term       => Searches contact first name, last name and acount name .              
  #
  # +@contacts+ is a WillPaginate::Collection.
  def list
    @sort = params[:sort] || "sfcontact.last_name"
    @order = params[:order]  || "DESC"
    if params[:company_id]
      @company = Sfaccount.find(params[:company_id])
      @contacts = @company.contacts.paginate(:per_page => 1, :page => params[:page], :order => "#{@sort} #{@order}")
    elsif params[:term]
      @term = "%#{params[:term]}%"
      @contacts = Sfcontact.paginate(:per_page => 50,:page => params[:page],
                                   :include => :company,
                                   :conditions => ["first_name LIKE ? or last_name LIKE ? or sfaccount.name LIKE ?", @term, @term, @term],
                                   :order => "#{@sort} #{@order}" )
    else
      @contacts =   if current_contact.privilege?(AppConstants::PRIVILEGE[:admin])
                        # all contacts
                        Sfcontact.paginate(:per_page => 50,:page => params[:page],
                                 :order => "#{@sort} #{@order}")
                    elsif current_contact.privilege?(AppConstants::PRIVILEGE[:support_admin])
                      # grab the contacts owned by the current user if a support admin
                      @contacts = current_contact.contacts.paginate(:order => "#{@sort} #{@order}",
                      :per_page => 50,:page => params[:page])
                    elsif current_contact.privilege?(AppConstants::PRIVILEGE[:super_user])
                      # grab the other contacts in the super user's company
                      @company = current_contact.company
                      @contacts = current_contact.company.contacts.paginate(:order => "#{@sort} #{@order}",
                      :per_page => 50,:page => params[:page])
                    end
      render(:action => 'list')
    end
  end
  alias index list
  
  # Authenicates the user with id +params[:id]+ and redirects to the default
  # home page.
  def authenticate
    if @contact = Sfcontact.find_by_sf_id(params[:id])
      cookies[:contact_id] = @contact.id
      cookies[:token] = { :value => @contact.token, :expires => AppConstants::COOKIE_TIME_LIMIT }
      flash[:notice] = "Now authenticated as #{@contact.name}"
      return redirect_to(home_url)
    else
      flash[:warning] = "couldn't find the contact."
      return redirect_to(:back)
    end
  end
  
  # Enables the user by setting 'portal_privilege' in both the associated Salesforce
  # record and the local record to 'Member'.
  def enable
    @contact = Sfcontact.find_by_sf_id(params[:id])
    sf_contact = Contact.find(@contact.id)
    sf_contact.portal_privilege__c = AppConstants::PRIVILEGE[:member]
    sf_contact.save_and_update
  end
end
