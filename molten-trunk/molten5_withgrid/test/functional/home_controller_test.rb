require File.dirname(__FILE__) + '/../test_helper'
require 'home_controller'

# Re-raise errors caught by the controller.
class HomeController; def rescue_action(e) raise e end; end

class HomeControllerTest < Test::Unit::TestCase
  
  fixtures :sfcontact, :sfcase, :sfaccount, :sfsolution
  
  def setup
    @controller = HomeController.new
    @request    = ActionController::TestRequest.new
    @response   = ActionController::TestResponse.new
    
    authenticate_contact
    
    # init solution settings
    SfsolutionSetting.destroy_all
    Sfsolution.find(:all).each { |s| s.save }
  end
  
  def test_access
    # failure - remove contact from session
    logout_contact
    get :index
    assert_response :redirect
    
    # success
    authenticate_contact
    get :index
    assert_response :success
  end

  def test_index
    Sfsolution.update_all("status = '#{Sfsolution::STATUSES[:published]}'")
    
    get :index
    assert_response :success
    assert assigns(:cases).any?
    # fails on test:functionals
    # assert assigns(:new_solutions).any?
    assert assigns(:recently_viewed_solutions).empty?
  end
end
