class CachingController < ApplicationController
  before_filter :set_model
  layout nil
  helper :cases
  helper :attachments
  helper :comments
  
  def sfcase
    # # expire the home 'recently updated cases' fragment
    # expire_fragment(:controller => 'home', :action => 'index', :part => 'cases', :contact_id => @model.contact.id )
    # 
    # # expire the show view
    # 
    # # expire the list of user support cases
    # expire_fragment(:controller => 'cases', :action => 'list', :part => 'cases', :contact_id => current_contact.id, :all_at_company => false )
    # 
    # # expire the list of all support cases
    # @model.contact.company.contacts.each do |contact|
    #   expire_fragment(:controller => 'cases', :action => 'list', :part => 'cases', :contact_id => contact.id, :all_at_company => true )
    # end
    # 
    # render :text => "Sfcase fragments updated."
  end
  
  def sfsolution
    # expire the homepage 'new solutions' if this a newly created solution
    if Sfsolution.find_new.include?(@model)
      expire_fragment(:controller => 'home', :action => 'index', :part => 'new_solutions' )
    end
  end
  
  def viewing
    # expire recently viewed solutions from the home page
    if @model.viewable.is_a?(Sfsolution)
      expire_fragment(:controller => 'home', :action => 'index', :part => 'recent_solutions', :contact_id => @model.sfcontact.id)
    end
    render :text => "Viewing fragments expired."
  end
  
  private
  
  def set_model
    @model = params[:action].camelize.constantize.find(params[:id])
  end
end
