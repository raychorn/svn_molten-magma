require File.dirname(__FILE__) + '/../test_helper'
require 'solutions_controller'

# Re-raise errors caught by the controller.
class SolutionsController; def rescue_action(e) raise e end; end

class SolutionsControllerTest < Test::Unit::TestCase
  
  fixtures :sfcontact, :sfsolution, :sfcatnode, :sfcatdata, :app_setting
  
  def setup
    @controller = SolutionsController.new
    @request    = ActionController::TestRequest.new
    @response   = ActionController::TestResponse.new
    
    authenticate_contact
    
    Sfsolution.find(:all).each { |s| s.save }
    
    @solution = sfsolution(:make_a_pizza).reload
  end
  
  def test_search
    # failure - no search term provided
    get :search
    assert_response :success
    assert assigns(:solutions).empty?
    assert_email_not_sent
    
    # test stripping
    term = "   tcl  "
    get :search, :term => term
    assert_response :success
    # assert_equal term.strip, assigns(:term)
    assert_email_not_sent
    
    # test parsing
    term = "DTC-317"
    get :search, :term => term
    assert_response :success
    assert_email_not_sent
    
    term = "INTERNAL SOFTWARE ERROR: assert(_model2group == 0)"
    get :search, :term => term
    assert_response :success
    # assert_email_sent
    
    # get :auto_complete_for_term, :term => term
    assert_response :success
    # assert_email_sent
    
    # term = "legalize%28%29&category_id=0"
    # get :search, :term => term
    #     assert_response :success
    #     # assert_email_sent
    #     
    #     get :auto_complete_for_term, :term => term
    #     assert_response :success
    # assert_email_sent
    
  end
  
  def test_rate
    # rate a solution w/o any counts
    xhr :post, :rate, :id => @solution.id, :rating => 'three'
    assert_response :success
    assert_equal 1, @solution.rating.reload.three
    
    # do it again
    xhr :post, :rate, :id => @solution.id, :rating => 'three'
    assert_response :success
    assert_equal 2, @solution.rating.reload.three
  end
  
  def test_category
    # top level category
    # get :category, :id => sfcatnode(:howto).id
    # assert_response :success
    # assert assigns(:category)
    # assert assigns(:solutions).any?
    
    # 2nd level category
    get :category, :id => sfcatnode(:howto_delete).id
    assert_response :success
    assert assigns(:category)
    # assert assigns(:solutions).any?
    
    # 3rd level category
    get :category, :id => sfcatnode(:howto_delete_comments).id
    assert_response :success
    assert assigns(:category)
    # assert assigns(:solutions).any?
  end

  def test_show
    Sfsolution.update_all("status = 'Published'")
    get :show, :id => @solution.id
    assert_response :success
    assert assigns(:solution)
  end
  
  def test_list
    get :list
    assert_response :success
    categories =  assigns(:categories)
  end
end
