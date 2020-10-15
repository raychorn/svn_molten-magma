class Admin::SolutionRelevancyController < AbstractAdminController

  before_filter :set_relevancy

  def edit
    render(:action => 'edit')
  end
  alias index edit
  
  def update
    if @relevancy.update_attributes(params[:relevancy])
      flash[:notice] = "Relevancy Updated."
    end
    render(:action => 'edit')
  end
  
  private
  
  def set_relevancy
    @relevancy = SolutionRelevancy.find(:first)
  end
end
