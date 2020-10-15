# for submitting cases to Salesforce
require 'net/http'

class CasesController < ProtectedController
  #################
  ### Behaviors ###
  #################
  helper :attachments
  helper :comments
  
  authorize :actions => [:index,:list,:show,:new,:toggle_case_viewable,:create,:edit,:suggested_solutions_and_cases]
  
  #################
  ### Constants ###
  #################
  SUBMIT_ACTIONS = {:preview => 'Preview', :submit => 'Submit'}

  ###############
  ### Actions ###
  ###############
  def list
    @sort = params[:sort]
    @order = params[:order]
    retrieve_cases
    render(:action => 'list')
  end
  alias index list
  
  def search
    @total, @cases = Sfcase.full_text_search(params[:term],current_contact,{:page => params[:page]})
    @cases = WillPaginate::Collection.create((params[:page] || 1),AppConstants::SOLUTIONS_PER_PAGE) do |pager|
      pager.replace(@cases)
      pager.total_entries = @total
    end
    render(:action => 'list')
  end
  
  def auto_complete_for_term
    @cases = Sfcase.full_text_search(params[:term],current_contact).last.slice(0..9)
    @cases.each { |c| c.subject = "\"" + c.subject.strip + "\""}
    render :inline => "<%= auto_complete_result(@cases, 'subject', 'blah') %>"
  rescue
    raise
    ErrorMailer.deliver_search_error(params[:term],$!)
    render :nothing => true
  end
  
  def group_cases(cases)
    cases = cases.group_by(&:status)
    ordered_cases = []
    AppConstants::CASE_SORT_ORDER.each do |status|
      cases.keys.each do |key|
        if key == status
          ordered_cases << [key,cases[key]]
        end
      end
    end
    ordered_cases
  end
  
  def export
    @sort = params[:sort]
    @order = params[:order]
    retrieve_cases
    e = Excel::Workbook.new
    cases = []
    
    @cases.each do |sfcase|
      cases << add_array_for_case(sfcase)
      logger.info "#{sfcase.case_number}: #{sfcase.aging_weeks__c}"
    end
    # raise @cases_grouped_by_status.map { |x| x.last }.flatten.join(', ')
    e.addWorksheetFrom2DArray("Support Cases", cases)

    send_data(e.build, :filename => "cases_#{Time.now.strftime("%m_%d_%y")}.xls")
  end
  
  # Creates a hash that is turned into a row into an Excel spreadsheet.
  # order: case_number subject status cr_status__c priority expedited_priority__c customer_priority__c customer_tracking__c expected_resolution_date__c version_number__c product__c component__c query_build_view__c workaround_available__c workaround_description__c description last_modified_date aging_weeks__c origin tape_out_date__c foundry__c speed_m_hz__c cell_count_k_objects__c owner_id
  def add_array_for_case(sfcase)
    [
      ['case_number' , sfcase.case_number],
      ['subject' , sfcase.subject],
      ['status' , sfcase.status],
      ['cr_status__c' , sfcase.cr_status__c],
      ['cr_number__c' , sfcase.cr_number__c],
      ['priority' , sfcase.priority],
      ['expedited_priority__c' , sfcase.expedited_priority__c],
      ['customer_priority__c' , sfcase.customer_priority__c],
      ['customer_tracking__c' , sfcase.customer_tracking__c],
      ['expected_resolution_date__c' , sfcase.expected_resolution_date__c],
      ['version_number__c' , sfcase.version_number__c],
      ['product__c' , sfcase.product__c],
      ['component__c' , sfcase.component__c],
      ['query_build_view__c' , sfcase.query_build_view__c],
      ['tape_out_date__c' , sfcase.tape_out_date__c],
      ['workaround_available__c' , sfcase.workaround_available__c],
      ['workaround_description__c' , sfcase.workaround_description__c],
      ['description' , sfcase.description],
      ['last_updated' , sfcase.last_updated__c],
      ['created_date', sfcase.created_date],
      ['aging_weeks__c', sfcase.aging_weeks__c],
      ['origin' , sfcase.origin],
      ['foundry__c' , sfcase.foundry__c],
      ['speed_m_hz__c' , sfcase.speed_m_hz__c],
      ['cell_count_k_objects__c', sfcase.cell_count_k_objects__c],
      ['owner_id' , sfcase.owner.name],
      ['contact_id', sfcase.contact.name],
      ['weekly_notes__c', sfcase.weekly_notes__c]
    ]
  end
  
  def set_all_cases
    cookies[:all_cases] = { :value => 'true', :expires => AppConstants::COOKIE_TIME_LIMIT }
  end
  
  def set_my_cases
    cookies.delete :all_cases
  end
  
  def all_cases
    params[:all] || cookies[:all_cases]
  end
  
  # Need to add status sorting
  def retrieve_cases
    # set options - sort/order/all
    options = {:sort => params[:sort], :order => params[:order]}
    options.delete_if { |key,value| value.blank? }
    options = {:sort => 'sfcase.last_modified_date', :order => 'DESC'}.merge(options)
    
    # build the sort sql
    sort_sql = options[:sort] + ' ' + options[:order] 
    if all_cases == 'true' and company = current_contact.company
      set_all_cases
      # owner sort is handled thru Ruby...could be 
      # either a Sfgroup or a Sfuser
      if options[:sort] == 'sfuser.last_name'
        cases = Sfcase.paginate(:per_page => AppConstants::SOLUTIONS_PER_PAGE, :page => (params[:page] || 1), :include => [:contact], 
        :conditions => ["sfcase.contact_id IN (?)",company.associated_contacts.map { |c| c.id  }])
        @cases = sort_cases_by_owner(cases,options)
      elsif options[:sort] == 'status'
        cases = Sfcase.find(:all, 
        :include => [:contact], 
        :conditions => ["sfcase.contact_id IN (?)",company.associated_contacts.map { |c| c.id  }])
        @cases = sort_cases_by_status(cases,options)
      else 
        @cases = Sfcase.paginate(:per_page => AppConstants::SOLUTIONS_PER_PAGE, :page => (params[:page] || 1), :include => [:contact], 
        :conditions => ["sfcase.contact_id IN (?)",company.associated_contacts.map { |c| c.id  }], 
        :order => sort_sql)
      end
    else
      set_my_cases
      if options[:sort] == 'sfuser.last_name'
        cases = Sfcase.find(:all, 
        :include => [:contact], 
        :conditions => "sfcase.contact_id = '#{current_contact.id}'")
        @cases = sort_cases_by_owner(cases,options)
      elsif options[:sort] == 'status'
        cases = Sfcase.find(:all, 
        :include => [:contact], 
        :conditions => "sfcase.contact_id = '#{current_contact.id}'")
        @cases = sort_cases_by_status(cases,options)
      else
        @cases = Sfcase.paginate(:per_page => AppConstants::SOLUTIONS_PER_PAGE, :page => (params[:page] || 1), 
        :include => [:contact], 
        :conditions => "sfcase.contact_id = '#{current_contact.id}'", 
        :order => sort_sql)
      end
    end
  end
  
  def offset
    AppConstants::SOLUTIONS_PER_PAGE * (page = params[:page].to_i and page > 0 ? page-1 : 0)
  end
  
  def sort_cases_by_status(cases,options)
    ordered_cases = []
    order = if options[:order] == 'ASC'
              AppConstants::CASE_SORT_ORDER
            else
              AppConstants::CASE_SORT_ORDER.reverse
            end
    order.each do |status|
      logger.info "Status: #{status}"
      cases.each_with_index do |support_case,index|
        logger.info "#{support_case.status} #{index} #{support_case.case_number}"
        if status == support_case.status
          ordered_cases << support_case
          cases.delete(support_case)
        end
      end
    end
    
    # add in cases that aren't of any of the specified groups
    cases = ordered_cases + cases
    
    WillPaginate::Collection.create((params[:page] || 1),AppConstants::SOLUTIONS_PER_PAGE) do |pager|
      pager.replace(cases[offset..(offset+AppConstants::SOLUTIONS_PER_PAGE)])
      pager.total_entries = cases.size
    end
  end
  
  def sort_cases_by_owner(cases,options)
    if options[:order] == 'ASC'
      cases.sort! { |x,y| x.owner.sort_name <=> y.owner.sort_name }
    else
      cases.sort! { |x,y| y.owner.sort_name <=> x.owner.sort_name }
    end
    WillPaginate::Collection.create((params[:page] || 1),AppConstants::SOLUTIONS_PER_PAGE) do |pager|
      pager.replace(cases[offset..(offset+AppConstants::SOLUTIONS_PER_PAGE)])
      pager.total_entries = cases.size
    end
  end
  
  def feed
    setting = SfcontactSetting.find_by_token(params[:id])
    headers["Content-Type"] = "application/xml"
    if setting.nil?
      @error_message = "An error occurred retrieving this RSS Feed."
      return render(:action => 'feed_error', :layout => false)
    else
      @contact = setting.sfcontact
      @cases = @contact.cases.find(:all, :limit => AppConstants::CASE_FEED_LIMIT)
      return render(:layout => false)
    end
  end
  
  def test
    #@mpost=MoltenPost.find_all
    @currentTime=Time.now
    #@currentTime=@currentTime+(7*60 * 60)+(3*60) @currentTime=@currentTime.gmtime+(5*30) @todate=@currentTime.strftime("%Y-%m-%dT%H:%M:%SZ") 
    @fromdate="2006-12-15T20:00:01Z"

    #@sfUpdatedMolten=MoltenPost.connection.get_updated("MoltenPost__c", "#{@fromdate}", "#{@todate}")
    @sfUpdatedMolten=MoltenPost.connection.get_deleted("MoltenPost__c", "#{@fromdate}", "2007-01-10T20:00:01Z")
  end
  
  def boom
    raise "boom"
  end

  def show
    @case = Sfcase.view(params[:id],current_contact)
  end
  
  def edit
    @case = Sfcase.find(params[:id])
  end
  
  def sfshow
    @case = Case.find(params[:id])
    render(:action => 'show')
  end
  
  def close
    @case = Sfcase.find(params[:id])
    if request.post?
      begin
        Case.connection.binding.assignment_rule_id = ""
        @case.close!(params[:state], current_contact, :comment => params[:comment], :rating => params[:rating])
      rescue
        raise
        flash[:warning] = $!
        return
      end
      return redirect_to(:action => 'show', :id => @case.id, :notice => "The case has been closed.")
    end
  end

  def new
    @case = Sfcase.new(params[:case])
  end
  
  def new_beta
    @case = Sfcase.new(params[:case])
  end
  
  # Provides suggested solutions and cases via AJAX when creating a new support case. 
  def suggested_solutions_and_cases
    search_term = params[:subject].to_s.strip
    case_id = params[:case_id]
    @suggested_cases_all = Sfcase.full_text_search(search_term,current_contact).last
    if case_id
      #@suggested_cases_all.delete_if {|c| c.subject == search_term}
      @suggested_cases_all.delete_if {|c| c.id == case_id}
    end
    @suggested_solutions_all = Sfsolution.full_text_search(search_term,current_contact,
                                             {

                                             },
                                             {
                                               :account_specific => :combine
                                             }
                                            ).last
    @suggested_cases = @suggested_cases_all.slice(0..4)
    @suggested_solutions = @suggested_solutions_all.slice(0..4)
    render :update do |page|
      if @suggested_solutions.any?
        logger.info "Found #{@suggested_solutions_all.size} solutions"
        page.replace_html "suggested_solutions_container", :partial => 'suggested_solutions'
        if @suggested_solutions_all.size > 5
           page.insert_html :bottom, "suggested_solutions_container",
                 link_to("More matching solutions...", "/solutions/search?term=" + search_term)
        end
      else
        page.replace_html "suggested_solutions_container", ''
      end
      if @suggested_cases.any?
        logger.info "Found #{@suggested_cases_all.size} solutions"
        page.replace_html "suggested_cases_container", :partial => 'suggested_cases'
        if @suggested_cases_all.size > 5
           page.insert_html :bottom, "suggested_cases_container",
                 link_to("More similar cases...", "/cases/search?term=" + search_term)
        end
      else
        page.replace_html "suggested_cases_container", ''
      end
      suggestions_text = ''
      suggestions_text = if @suggested_solutions.any? and @suggested_cases.any?
                            "Found #{@suggested_solutions_all.size} matching solutions and #{@suggested_cases_all.size} similar cases."
                         elsif @suggested_solutions.any?
                            "Found #{@suggested_solutions_all.size} matching solutions."
                         elsif @suggested_cases.any?
                            "Found #{@suggested_cases_all.size} similar cases."
                         else 
                           ""
                         end
      suggestions_text = "<span class=\"suggestions_results\">" + suggestions_text + "</span>"
      page.replace_html "suggestions_box", suggestions_text
#      page.delay(5) do 
#          page.hide "suggestions_box"
#          page.replace_html "suggestions_box", "Searching..."
#      end
    end
  end
  
  def create
    @case = Sfcase.new(params[:case])
    @case.account = current_contact.company
    @case.validate_case_attributes = true
    if @case.valid?
      if preview?
        render(:action => 'show')
      else
        case_params = params[:case].merge!({:type => params[:case][:sf_type]})
        case_params.delete("sf_type")
        case_params.merge!(:priority => params[:case][:customer_priority__c])
        Case.connection.binding.assignment_rule_id = "01Q3000000000XiEAI"
        Case.connection.binding.trigger_user_email = true      # send email to case owner
        Case.connection.binding.trigger_other_email = true      # send email to case contact
        @case = Case.new(case_params).save_and_clone
        flash[:notice] = "Your case was submitted successfully."
        return redirect_to(:action => 'index', :all => cookies[:all_cases],
                           :notice => "Your case was submitted successfully. A copy of the support case has been emailed to #{current_contact.email}.")
      end
    else
      return render(:action => 'new')
    end
  end
  
  def update
    Case.connection.binding.assignment_rule_id = ""
    @case = Sfcase.find(params[:id])
    if @case.update_attributes_and_sync(params[:case]) 
      @case.set_update_time!(@case.synced_record.last_modified_date)
      @case.reload.update_salesforce_attribute('last_updated__c')
      flash[:notice] = "The case has been updated."
      return redirect_to(:action => 'show', :id => @case)
    else
      return render(:action => 'edit')
    end
  end
  
  def toggle_case_viewable
    current_contact.toggle_case_viewable(params[:status])
  end
  
  def modify_column_display
    @setting = current_contact.settings.case_columns_setting
    if request.post?
      if @setting.update_attributes(params[:setting])
        flash[:notice] = "Your settings have been updated."
        redirect_to params[:from]
      end
    end
  end
  
  private
  
  def preview?
    params[:commit] == SUBMIT_ACTIONS[:preview]
  end
  
  # Grabs only those attributes specified in +AppConstants::CASE_FIELD_MAPPING+ and converts them into a params string.
  def salesforce_params
    params = {:encoding => 'UTF-8', :orgid => '00D3000000002QQ', :recordType => '01230000000001X'}
    
    # in debug mode?
    if AppSetting.config("Salesforce Form Submissions") == AppSetting::SALESFORCE_FORM_SUBMISSIONS[:debug]
        logger.info("Adding case debug params")
        params.merge!({:debug => 1})
        params.merge!({:debugEmail => AppSetting.config("Technical Support Email")})
    end
    
    AppConstants::CASE_FIELD_MAPPING.each do |key,value|
      params.merge!({value => @case.attributes[key.to_s]})
    end
    logger.info("Created Support Case Params: #{params.to_a.map { |key_value| "#{key_value.first}: #{key_value.last}\n" }}")
    return params
  end
  
  # Submits the case to Salesforce.
  def submit_case_to_salesforce
    # don't submit if in 'no submit' mode
    return if AppSetting.config("Salesforce Form Submissions") == AppSetting::SALESFORCE_FORM_SUBMISSIONS[:no_submit]
    response = Net::HTTP.post_form(URI.parse('http://www.salesforce.com/servlet/servlet.WebToCase'),
                                  salesforce_params)
    logger.info("Response from Salesforce after submitting case: #{response}")
  end
end
