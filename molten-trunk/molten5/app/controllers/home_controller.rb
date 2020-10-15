class HomeController < ProtectedController
  ATTACH_COLS = {:file_name => 'file_name', :uploaded_by => 'uploaded_by', :uploaded => 'uploaded'}
  ATTACH_MAPPING = {'file_name' => 'sfattach.name', 'uploaded_by' => 'last_name', 'uploaded' => 'sfattach.created_date'}
  def index
    @marketing = SfmoltenPost.check_marketing_message_for_contact(current_contact)
    # BEGIN: Debug code... this line replaces the line above to cause marketing messages to always appear.
    #@marketing = SfmoltenPost.find(:first)
    # END!   Debug code...
    @cases = current_contact.recently_updated_cases
    @popular_solutions = Sfsolution.find_popular_in_range(current_contact).map(&:first)
    @articles = SfmoltenPost.find_articles(:limit => AppConstants::ARTICLE_LIMIT)
    @new_solutions = Sfsolution.find_new(current_contact)
    @recently_viewed_solutions = current_contact.recent_sfsolutions
  end
  
  def custom
    @solution = current_contact.custom_home_page
    
    @sort = params[:sort] || ATTACH_COLS[:uploaded]
    @order = params[:order] || 'ASC'
    if params[:term] and !params[:term].strip.blank?
      @term = params[:term].strip
      @attachments = Sfattach.search(@solution, @term,sort_and_order_sql.merge({:page => params[:page]}))
    else
      @attachments = Sfattach.search(@solution, nil,sort_and_order_sql.merge({:page => params[:page]}))
    end
  end
  
  # To protect against SQL Injection
  def sort_and_order_sql
    {:sort => ATTACH_MAPPING[@sort], :order => @order}
  end
end
