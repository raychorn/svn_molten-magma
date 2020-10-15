require File.dirname(__FILE__) + '/../../test_helper'
require 'admin/contacts_controller'

# Re-raise errors caught by the controller.
class Admin::ContactsController; def rescue_action(e) raise e end; end

class Admin::ContactsControllerTest < Test::Unit::TestCase
  
  fixtures :sfcontact, :sfaccount
  
  def setup
    @controller = Admin::ContactsController.new
    @request    = ActionController::TestRequest.new
    @response   = ActionController::TestResponse.new
    
    @derek = sfcontact(:derek_haynes)
    
    authenticate_contact(sfcontact(:derek_haynes))
  end

  def test_list
    get :list
    assert_response :success
    
    # sort by last name
    get :list, :sort => 'last_name', :order => 'DESC'
    assert_response :success
  end
  
  def test_authenticate
    new_user = sfcontact(:derek)
    get :authenticate, :id => new_user.id
    assert_redirected_to "action"=>"index", "controller"=>"home"
    assert_equal new_user, current_contact
    assert_not_nil flash[:notice]
  end
  
  def test_access
    assert current_contact.privilege?(AppConstants::PRIVILEGE[:admin])
    
    # allow entry - an admin
    get :list
    assert_response :success
    
    # allow entry - a support admin
    @derek.update_attribute('portal_privilege__c', AppConstants::PRIVILEGE[:support_admin])
    assert !@derek.privilege?(AppConstants::PRIVILEGE[:admin])
    assert @derek.privilege?(AppConstants::PRIVILEGE[:support_admin])
    get :list
    assert_response :success
    
    # allow entry - a super user
    @derek.update_attribute('portal_privilege__c', AppConstants::PRIVILEGE[:super_user])
    assert !@derek.privilege?(AppConstants::PRIVILEGE[:support_admin])
    assert @derek.privilege?(AppConstants::PRIVILEGE[:super_user])
    get :list
    assert_response :success
    
    # don't allow entry - a member
    @derek.update_attribute('portal_privilege__c', AppConstants::PRIVILEGE[:member])
    assert !@derek.privilege?(AppConstants::PRIVILEGE[:super_user])
    assert @derek.privilege?(AppConstants::PRIVILEGE[:member])
    get :list
    assert_redirected_to '/contact/login_form'
  end
end
