require File.dirname(__FILE__) + '/../../test_helper'
require 'admin/settings_controller'

# Re-raise errors caught by the controller.
class Admin::SettingsController; def rescue_action(e) raise e end; end

class Admin::SettingsControllerTest < Test::Unit::TestCase
  
  fixtures :sfcontact, :app_setting
  
  def setup
    @controller = Admin::SettingsController.new
    @request    = ActionController::TestRequest.new
    @response   = ActionController::TestResponse.new
    
    authenticate_contact
    
    @setting = AppSetting.find(:first)
  end

  def test_list
    get :list
    assert_response :success
    assert assigns(:settings).any?
  end
  
  def test_edit
    get :edit, :id => @setting.id
    assert_response :success
    assert assigns(:setting)
  end
  
  def test_update
    # failure - setting invalid
    post :update, :id => @setting.id, :setting => {:name => ""}
    assert_response :success
    assert !assigns(:setting).valid?
    
    # success
    post :update, :id => @setting.id, :setting => {:name => "updated name"}
    assert_response :redirect
    assert_equal "updated name", @setting.reload.name
  end
end
