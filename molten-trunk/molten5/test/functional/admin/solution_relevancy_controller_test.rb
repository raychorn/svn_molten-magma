require File.dirname(__FILE__) + '/../../test_helper'
require 'admin/solution_relevancy_controller'

# Re-raise errors caught by the controller.
class Admin::SolutionRelevancyController; def rescue_action(e) raise e end; end

class Admin::SolutionRelevancyControllerTest < Test::Unit::TestCase
  
  fixtures :solution_relevancy, :sfcontact, :sfaccount
  
  def setup
    @controller = Admin::SolutionRelevancyController.new
    @request    = ActionController::TestRequest.new
    @response   = ActionController::TestResponse.new
    
    @derek = sfcontact(:derek_haynes)
    
    authenticate_contact(@derek)
  end

  def test_edit
    get :edit
    assert_response :success
  end
  
  def test_update
    # failure 
    post :update, :relevancy => {:rating_value_one => ''}
    assert_response :success
    assert !assigns(:relevancy).valid?
    
    # success
    post :update, :relevancy => {:rating_value_one => 30}
    assert_response :success
    assert assigns(:relevancy).valid?
  end
end
