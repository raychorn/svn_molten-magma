module  ActionController
  module Cookies
    def cookies
      CookieJar.new(self)
    end
  end
end


class ActionController::Base
  # Use this inside a controller to limit access to authenticated contacts.
  # Usage:
  #   authorize => a user must be authenticated to access any action in the controller. 
  #   authorize :condition_method => :is_a_admin? => +current_user.is_a_admin?+ must be true to grant access.
  #   authorize :actions => [:account] => only protect the +account+ action.
  def self.authorize(options = {})
    options = {:condition_method => nil, :actions => []}.merge(options)
    
    before_filter :cookie_auth
    
    if options[:actions].any?
      before_filter :login_required, :only => options[:actions]
    else
      before_filter :login_required
    end
    
    if options[:condition_method]
      module_eval <<-CODE
        def authorized?
          current_user.send(#{options[:condition_method]})
        end
      CODE
    end
    
    module_eval <<-CODE
      # attempts to authenticate by cookie. a contact is only authenticated via cookie 
      # if no contact is in the session.
      def cookie_auth
        return if current_contact or cookies[:contact_id].nil? or cookies[:token].nil?
        if @contact = Sfcontact.authenticate_by_token(cookies[:contact_id], cookies[:token])
      	  @session[:contact_id] = @contact.id
      	end
      end
    CODE
  end
end

module  AuthenticationSystem
  def login_required
    unless current_contact and authorized?
      session[:intended_uri] = request.request_uri
      redirect_to(:controller => '/contact', :action => "login_form", :notice => params[:notice]) and return false
    end
    authorized?
  end
  
  # True if in the admin area.
  def in_admin_area?
    params[:controller] =~ /admin/ or @admin_area == true
  end
  
  def current_contact
    id = cookies['contact_id'] || (!response.cookies.nil? ? response.cookies['contact_id'] : nil) || (!request.cookies.nil? ? request.cookies['contact_id'] : nil)
    Sfcontact.find_by_sf_id(id)
  end
  
  # Override this method to add fine-grained access control. 
  def authorized?
    true
  end
  
  # Generates the default redirection. 
  def default_url
    return nil if current_contact.nil?
    url_for(:controller => 'home')
  end
  
  # Redirects the user to the default action if the contact isn't being blocked by a filter...
  # otherwise, the contact is redirected to +session[:intended_uri]+.
  def redirect_to_stored_or_default(default)
    if session[:intended_uri].nil?
      if (RAILS_ENV == 'production') and (request.env['SERVER_NAME'] != 'localhost')
        redirect_to :protocol => 'https://', :controller => '/home'
      else
        redirect_to :controller => '/home'
      end
    else
      redirect_to session[:intended_uri]
      session[:intended_uri] = nil
    end
  end
end