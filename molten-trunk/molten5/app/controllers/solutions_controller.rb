require "#{RAILS_ROOT}/vendor/faster_csv/lib/faster_csv"

class SolutionsController < ProtectedController
  helper :attachments
  helper :comments
  include SolutionViewing
  
  FUZZY = '~0.5'

  def list
    unless read_fragment(:action => 'index', :part => 'categories') and read_fragment(:action => 'index', :part => 'search')
      @categories = Sfcatnode.top_level
    end
    render(:action => 'list')
  end
  alias index list
  
  def show
    @solution = Sfsolution.view(params[:id],current_contact)
    
    if !@solution.viewable? or (!@solution.portal_account_name_id__c.blank? and !current_contact.account.all_in_tree.map { |a| a.id }.include?(@solution.portal_account_name_id__c))
      flash[:warning] = "This solution is not available for viewing."
      return redirect_to(:action => 'list', :warning => "This solution is not available for viewing.")
    end
  end
  
  def category
    @category = Sfcatnode.find(params[:id], :include => [:category_datas])
    @solutions = @category.solutions_for_contact(current_contact).paginate(:per_page => AppConstants::SOLUTIONS_PER_PAGE,
                                   :page => params[:page])
                                   
  end
  
  def rate
    @solution = Sfsolution.find(params[:id])
    @solution.rate!(params[:rating])
  end

  def recent
     @total, @solutions = Sfsolution.new_solutions_in_range(current_contact)
     @solutions = paginate_collection(@solutions,:per_page => AppConstants::SOLUTIONS_PER_PAGE,
                                     :page => params[:page], :total => @total)
                                 
  end
  
  def test_search
    @results = []
    FCSV.foreach( "#{RAILS_ROOT}/files/search_solutions.csv",
                  :headers           => true ) do |line|
      import = line.to_hash
      set_term(import['term'])

      @total, @solutions = Sfsolution.full_text_search(@term,current_contact,
               {
                 :include => [:settings], 
                 :order => "sfsolution_setting.relevancy DESC",
                 :page => (params[:page]||1)
               }
              )
      
      @results << {:term => import['term'], :count => @total, :sf_count => import['results_count']}
    end # FCSV.each
    @admin_area = true
  end
  
  def search
    set_term   
    if @term.blank?
      flash[:warning] = "Please enter a search term."
      @solutions = WillPaginate::Collection.create(1,AppConstants::SOLUTIONS_PER_PAGE) do |pager|
        pager.replace([])
        pager.total_entries = 0
      end
    else     
      account_specific = if params[:account_specific] == '1'
                              :only
                         elsif params[:account_specific] == '0'
                              :skip
                         else
                              :separate
                         end
      @total_specific, @solutions_specific, @total, @solutions = Sfsolution.full_text_search(@term,current_contact,
               {
                 :include => [:settings], 
                 :order => "sfsolution_setting.relevancy DESC",
                 :page => (params[:page]||1)
               },
               {
                 :account_specific => account_specific
               }
              )
      @solutions_specific = WillPaginate::Collection.create((params[:page] || 1),AppConstants::SOLUTIONS_PER_PAGE) do |pager|
        pager.replace(@solutions_specific)
        pager.total_entries = @total_specific
      end
      
      @solutions = WillPaginate::Collection.create((params[:page] || 1),AppConstants::SOLUTIONS_PER_PAGE) do |pager|
        pager.replace(@solutions)
        pager.total_entries = @total
      end
      
      SolutionSearchLog.create!(:contact => current_contact, :term => @term, :results_count => @solutions.size )
    end
    @term = @original_term
  rescue  RegexpError
    flash[:warning] = "Search is being configured at this moment."
    ErrorMailer.deliver_search_error(params[:term],$!)
  rescue
    @solutions = WillPaginate::Collection.new(1,AppConstants::SOLUTIONS_PER_PAGE) do |pager|
      pager.replace([])
      pager.total_entries = 0
    end
    flash[:warning] = "An error occured executing this search. We have been notified of the error."
    ErrorMailer.deliver_search_error(params[:term],$!)
  end
  
  def search_regex
    Regexp.new(AppSetting.config("Solutions Search RegEx"))
  end
  
  def auto_complete_for_term
    set_term
    
    @solutions = Sfsolution.full_text_search(@term,current_contact,
                                             {
                                               :order => "solution_name"
                                             },
                                             {
                                               :account_specific => :combine
                                             }
                                            ).last.slice(0..9)
    @solutions.each { |s| s.solution_name = "\"" + s.solution_name.strip + "\""}
    render :inline => "<%= auto_complete_result(@solutions, 'solution_name', 'blah') %>"
  rescue
    ErrorMailer.deliver_search_error(params[:term],$!)
    render :nothing => true
  end

  def feed
    setting = SfcontactSetting.find_by_token(params[:id])
    headers["Content-Type"] = "application/xml"
    if setting.nil?
      @error_message = "An error occurred retrieving this RSS Feed."
      return render(:action => 'feed_error', :layout => false)
    else
      @contact = setting.sfcontact
      @solutions = Sfsolution.find_new(current_contact)
      return render(:layout => false)
    end
  end
  
  def insert
    SalesforceWalker.insert_new(:classes => [Solution])
    render :nothing => true
  end
  
  private
  
  def pages_for(size, options = {})
    default_options = {:per_page => AppConstants::SOLUTIONS_PER_PAGE}
    options = default_options.merge options
    pages = Paginator.new self, size, options[:per_page], (params[:page]||1)
    return pages
  end
  
  # Sets +@term+ and sanitizes the term.
  # ferret has problems with '-'
    def set_term(term = params[:term])
      if term
        @original_term = term.dup
        @term = term
        @term = term.gsub(/\W/, ' ')
        @term = term.gsub(/([\]\[\~\{\}\!\:\&\|])/, '')
        @term.strip!
        @term.dump
        terms = @term.split(' ')
#        terms.reject! { |t| t == 'OR' or t == 'AND'}
#        terms.map!{ |t| "*"+t+"*"}
#        @term = terms.join(' OR ')
#        @term = "*" + @term + "*"
#        @term = "\"" + @term + "\""
#        @term << FUZZY
      end
    end
  
  # Removes any solutions not inside the specified +@category+ if the category is not the root
  # category. 
  def remove_solutions_out_of_category
    cat = Sfcatnode.find(params[:category_id])
    @solutions.reject! { |sol| !sol.category_tree.include?(cat)  }
  rescue
  end
end
