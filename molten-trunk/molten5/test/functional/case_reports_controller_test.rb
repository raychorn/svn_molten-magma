require File.dirname(__FILE__) + '/../test_helper'
require 'case_reports_controller'

# Re-raise errors caught by the controller.
class CaseReportsController; def rescue_action(e) raise e end; end

class CaseReportsControllerTest < Test::Unit::TestCase
  
  fixtures :sfaccount, :sfcontact, :case_report
  
  def setup
    @controller = CaseReportsController.new
    @request    = ActionController::TestRequest.new
    @response   = ActionController::TestResponse.new
    
    # put user in session
    authenticate_contact
    
    # Create contact setting records
    Sfcontact.find(:all).each { |c| c.save }
  end
  
  def test_create_new_saved_reports
    post :save_report,
      :order => 'DESC', :sort => 'customer_priority__c', :status => ['Open'],
      :case_report => {:name => 'Descended Open', :shared => '1'},
      :query => '&order=DESC&&sort=customer_priority__c&&status[]=Open&'
    last = CaseReport.find(:first, :order => 'created_at DESC')
    assert_redirected_to :controller => 'cases', :action => 'report', :id => last.id
  end
  
  def test_update_existing_saved_reports
    post :save_report,
      :order => 'DESC', :sort => 'customer_priority__c', :status => ['Open'],
      :case_report => {:id => '1', :shared => '1'},
      :query => '&order=DESC&&sort=customer_priority__c&&status[]=Open&'
    assert_redirected_to :controller => 'cases', :action => 'report', :id => 1
  end
  
  def test_delete_saved_report_returns_to_list_beta_with_same_options_as_report
    initial_count = CaseReport.count
    delete :destroy, :id => '1'
    assert_equal initial_count-1, CaseReport.count
    assert_response :success
  end
  
end
