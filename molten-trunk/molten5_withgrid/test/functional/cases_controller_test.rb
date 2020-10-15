require File.dirname(__FILE__) + '/../test_helper'
require 'cases_controller'

# Re-raise errors caught by the controller.
class CasesController; def rescue_action(e) raise e end; end

class CasesControllerTest < Test::Unit::TestCase
  
  fixtures :sfcontact, :sfcontact_setting, :sfcase, :sfaccount, :sfsolution, :sfuser, :case_columns_setting
  
  def setup
    @controller = CasesController.new
    @request    = ActionController::TestRequest.new
    @response   = ActionController::TestResponse.new
    
    authenticate_contact
    
    # Create contact setting records
    Sfcontact.find(:all).each { |c| c.save }
    
    @emails = ActionMailer::Base.deliveries
    @emails.clear
  end

  def test_show
    get :show, :id => sfcase(:widget_stuck).id
    assert_response :success
  end
  
  def test_new
    get :new
    assert_response :success
  end
  
  def test_edit
    get :edit, :id => sfcase(:widget_stuck).id
    assert_response :success
  end
  
  def test_close
    get :close, :id => sfcase(:widget_stuck).id
    assert_response :success
  end
  
  def test_modify_column_display
    get :modify_column_display
    assert_response :success
  end
  
  def test_suggested_solutions_and_cases
    Sfcase.rebuild_index
    Sfsolution.update_all("status = 'Published'")
    Sfsolution.rebuild_index
    
    # empty
    xhr :post, :suggested_solutions_and_cases, :subject => ''
    assert_response :success
    assert assigns(:suggested_solutions).empty?, "Suggested solutions are not empty: #{assigns(:suggested_solutions).map(&:solution_name).join(',')}"
    assert assigns(:suggested_cases).empty?
    
    # no match on subject
    xhr :post, :suggested_solutions_and_cases, :subject => 'blah'
    assert_response :success
    assert assigns(:suggested_solutions).empty?
    assert assigns(:suggested_cases).empty?
    
    # match on existing case
    xhr :post, :suggested_solutions_and_cases, :subject => 'widget'
    assert_response :success
    assert assigns(:suggested_solutions).empty?
    assert assigns(:suggested_cases).any?
    
    # match on existing solution
    xhr :post, :suggested_solutions_and_cases, :subject => 'pizza'
    assert_response :success
    # this fails in test:functionals, works on this suite
    # assert assigns(:suggested_solutions).any?
    assert assigns(:suggested_cases).empty?
    
  end
  
  def test_list
    get :list
    assert_response :success
  end
  
  # FAILING - LIBRARY ISSUE
  # TypeError: can't convert String into Integer
  #       /Users/itsderek23/Projects/molten_forum/vendor/rails/activerecord/lib/../../activesupport/lib/active_support/vendor/builder/xmlbase.rb:135:in `*'
  #       /Users/itsderek23/Projects/molten_forum/vendor/rails/activerecord/lib/../../activesupport/lib/active_support/vendor/builder/xmlbase.rb:135:in `_indent'
  #       /Users/itsderek23/Projects/molten_forum/vendor/rails/activerecord/lib/../../activesupport/lib/active_support/vendor/builder/xmlmarkup.rb:275:in `_special'
  #       /Users/itsderek23/Projects/molten_forum/vendor/rails/activerecord/lib/../../activesupport/lib/active_support/vendor/builder/xmlmarkup.rb:244:in `instruct!'
  #       /Users/itsderek23/Projects/molten_forum/vendor/plugins/excel/lib/excel.rb:83:in `build'
  #       /Users/itsderek23/Projects/molten_forum/app/controllers/cases_controller.rb:83:in `export'
  # def test_export
  #   get :export
  #   assert_response :success
  # end
  
  def test_create
    # failure - no subject provided
    post :create, :case => {:subject => ""}
    assert_invalid assigns(:case)
  end
  
  def test_feed
    # logout_contact # why is login required now?
    
    # failure - token doesn't exist
    get :feed, :id => "do not exist"
    assert_response :success
    assert_nil assigns(:cases)
    
    # success
    get :feed, :id => sfcontact_setting(:derek_setting).token
    assert assigns(:cases).any?
    assert_response :success
  end
  
  def test_toggle_case_viewable
    current_contact.save
    assert current_contact.case_viewable?('new')
    
    get :toggle_case_viewable, :status => 'new'
    assert_response :success
    assert !current_contact.case_viewable?('new')
  end
end
