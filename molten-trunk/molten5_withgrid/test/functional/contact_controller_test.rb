require File.dirname(__FILE__) + '/../test_helper'
require 'contact_controller'

# Re-raise errors caught by the controller.
class ContactController; def rescue_action(e) raise e end; end

class ContactControllerTest < Test::Unit::TestCase
  
  fixtures :sfcontact, :sfssl
  
  def setup
    @controller = ContactController.new
    @request    = ActionController::TestRequest.new
    @response   = ActionController::TestResponse.new
    
    @derek = sfcontact(:derek_haynes)
    # init settings
    Sfcontact.find(:all).each { |c| c.save }
    
    @emails = ActionMailer::Base.deliveries
    @emails.clear
  end
  
  def test_access
    # settings is protected
    get :settings
    assert_response :redirect
    
    # login not protected
    get :login
    assert_response :success
    
    # login form not protected
    get :login_form
    assert_response :success
  end
  
  def test_signup
    get :signup
    assert_response :success
  end
  
  def test_forgot_password
    get :forgot_password
    assert_response :success
  end
  
  def test_retrieve_password
    # failure - no email address provided
    post :retrieve_password
    assert_forgot_password_error
    
  
    # failure - no email match
    post :retrieve_password, :email => "no_exist@test.com"
    assert_forgot_password_error
    
    # success
    post :retrieve_password, :email => @derek.email, :token => @derek.token
    assert_response :success
    assert @emails.any?
  end
  
  def test_update_password_with_token
    @response.cookies[:contact_id] = nil
    assert_nil current_contact
    
    # failure - invalid user id
    post :update_password, :id => 9999, :token => @derek.token, 
                           :password => "baseball", :password_confirmation => "football"
    assert_redirected_to '/'
    assert_not_nil flash[:warning]
    
    # failure - invalid token
    post :update_password, :id => @derek.id, :token => 'abc', 
                           :password => "baseball", :password_confirmation => "football"
    assert_redirected_to '/'
    assert_not_nil flash[:warning]
    
    # failure - pw's don't match
    post :update_password, :id => @derek.id, :token => @derek.token, 
                           :password => "baseball", :password_confirmation => "football"
    assert_response :success
    assert_template 'contact/change_password'
    assert assigns(:contact)
     
    # failure - pw's blank
    post :update_password, :id => @derek.id, :token => @derek.token, 
                           :password => "", :password_confirmation => ""
    assert_response :success
    assert_template 'contact/change_password'
    assert assigns(:contact)
    
    # success
    post :update_password, :id => @derek.id, :token => @derek.token, 
                           :password => "baseball", :password_confirmation => "baseball"
    assert_redirected_to '/'
    assert_not_nil flash[:notice]
    assert_equal current_contact, @derek
    assert Sfcontact.authenticate(@derek.email,"baseball")
  end
  
  def test_confirm
    # failure - user with id doesn't exist
    get :confirm, :id => 123233, :token => sfcontact(:derek).token
    assert_response :success
    assert_not_nil flash[:warning]
    
    # failure  user with token doesn't exist
    get :confirm, :id => sfcontact(:derek).id, :token => 'dfdsfdsf'
    assert_response :success
    assert_not_nil flash[:warning]
    
    # success
    get :confirm, :id => sfcontact(:derek).id, :token => sfcontact(:derek).token
    assert_redirected_to :controller => 'contact', :action => 'settings'
    # assert_not_nil flash[:notice]
    assert_equal sfcontact(:derek), current_contact
    
    # failure - user tries to confirm again
    get :confirm, :id => sfcontact(:derek).id, :token => sfcontact(:derek).token
    # assert_response :success
    # assert_not_nil flash[:warning]
  end
  
  def test_update_password_with_authenticated_user
    @request.cookies['contact_id'] = @derek.id
    assert_equal @derek, current_contact
    
    # failure - pw's don't match
    post :update_password, :password => "baseball", :password_confirmation => "football"
    assert_response :success
    assert_template 'contact/settings'
    
    # failure - pw's blank
    post :update_password, :password => "", :password_confirmation => ""
    assert_response :success
    assert_template 'contact/settings'
    
    # success
    post :update_password, :password => "baseball", :password_confirmation => "baseball"
    assert_template 'contact/settings'
    assert Sfcontact.authenticate(@derek.email,"baseball")
  end
  
  def test_settings
    # failure - not logged in
    assert_nil current_contact
    get :settings
    assert_response :redirect

    # success
    @request.cookies['contact_id'] = @derek.id
    assert current_contact
    get :settings
    assert_response :success
    assert assigns(:contact)
  end
  
  def test_update
    
  end

  def test_login
    # failure - invalid email
    post :login, :email => "sadfdsaf", :password => @derek.portal_password__c
    assert_response :success
    assert_not_nil flash[:warning]
    
    # failure - invalid password
    post :login, :email => @derek.email, :password => "invalid"
    assert_response :success
    assert_not_nil flash[:warning]
    
    # failiure - no pw provided
    post :login, :email => @derek.email, :password => ""
    assert_response :success
    assert_not_nil flash[:warning]
    
    # success
    post :login, :email => @derek.email, :password => @derek.portal_password__c,
                 :contact_time => '1182477286470'
    assert_response :redirect
    assert_not_nil current_contact
    assert_not_nil @response.cookies['time_offset']
  end
  
  def test_login_sf
    # failure - contact id doesn't exist
    post :login_from_sf, :id => 'invalid'
    assert_response :success
    assert_nil current_contact
    
    # success
    post :login_from_sf, :id => @derek.sf_id
    assert_response :redirect
    assert_not_nil current_contact
  end
  
  def test_logout
    get :logout
    assert_response :redirect
    assert_nil current_contact
  end
  
  private
  
  def assert_forgot_password_error
    assert_response :success
    assert_not_nil flash[:warning]
  end
end
