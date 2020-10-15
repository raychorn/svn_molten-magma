ActionController::Routing::Routes.draw do |map|
  # The priority is based upon order of creation: first created -> highest priority.
  
  # Sample of regular route:
  # map.connect 'products/:id', :controller => 'catalog', :action => 'view'
  # Keep in mind you can assign values other than :controller and :action

  # Sample of named route:
  # map.purchase 'products/:id/purchase', :controller => 'catalog', :action => 'purchase'
  # This route can be invoked with purchase_url(:id => product.id)

  # You can have the root of your site routed by hooking up '' 
  # -- just remember to delete public/index.html.
  # map.connect '', :controller => "welcome"
  map.home '', :controller => 'home'
  
  map.admin '/admin', :controller => 'admin/contacts'

  # Allow downloading Web Service WSDL as a file with an extension
  # instead of a file named 'wsdl'
  map.connect ':controller/service.wsdl', :action => 'wsdl'
  
  map.connect 'contact/status/:email', :controller => 'contact', :action => 'status'
  
  #############
  ### Beast ###
  #############
  map.open_id_complete 'session', :controller => "session", :action => "create", :requirements => { :method => :get }
  map.resource :session
  
  map.resources :users, :member => { :admin => :post }, :collection => {:active => :get} do |user|
    user.resources :moderators
  end
  
  map.resources :forums do |forum|
    forum.resources :topics, :name_prefix => nil do |topic|
      topic.resources :posts, :name_prefix => nil
      topic.resource :monitorship, :controller => :monitorships, :name_prefix => nil
    end
  end
  
  map.resources :forum_signup, :collection => {:complete => :any}

  map.resources :posts, :name_prefix => 'all_', :collection => { :search => :get, :recent => :get, :abusive => :get },
                        :member => {:report => :put, :clear_abuse_counter => :put, :mark_as_abusive => :put}

  map.resources :topics, :collection => { :active => :get }, :name_prefix => 'all_'

  %w(user forum).each do |attr|
    map.resources :posts, :name_prefix => "#{attr}_", :path_prefix => "/#{attr.pluralize}/:#{attr}_id"
  end

  map.beast_home 'forums', :controller => 'forums', :action => 'index'
  map.signup   'signup',        :controller => 'users',   :action => 'new'
  map.settings 'settings',      :controller => 'users',   :action => 'edit'
  map.activate 'activate/:key', :controller => 'users',   :action => 'activate'
  map.login    'login',         :controller => 'session', :action => 'new'
  map.logout   'logout',        :controller => 'session', :action => 'destroy'
  map.with_options :controller => 'posts', :action => 'monitored' do |map|
    map.formatted_monitored_posts 'users/:user_id/monitored.:format'
    map.monitored_posts           'users/:user_id/monitored'
  end

  map.exceptions 'logged_exceptions/:action/:id', :controller => 'logged_exceptions', :action => 'index', :id => nil
  
  ### END BEAST ###
  
  # Install the default route as the lowest priority.
  map.connect ':controller/:action/:id'
  map.connect ':controller/:action'
  
end
