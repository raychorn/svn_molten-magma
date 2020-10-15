require File.dirname(__FILE__) + '/../test_helper'
require 'articles_controller'

# Re-raise errors caught by the controller.
class ArticlesController; def rescue_action(e) raise e end; end

class ArticlesControllerTest < Test::Unit::TestCase
  fixtures :sfcontact, :sfmolten_post
  def setup
    @controller = ArticlesController.new
    @request    = ActionController::TestRequest.new
    @response   = ActionController::TestResponse.new
    
    # put user in session
    authenticate_contact
    
    # Create contact setting records
    Sfcontact.find(:all).each { |c| c.save }
  end

  def test_list
    get :list
    assert_response :success
    assert assigns(:articles)
  end
  
  def test_sidebar
    get :sidebar
    assert_response :success
    assert assigns(:articles)
  end
  
  def test_show
    do_create_article
    get :show, :id => SfmoltenPost.find_articles.first.id
    assert_response :success
    assert assigns(:article)
  end
  
  private
  
  def do_create_article
    SfmoltenPost.create!(:record_type_id => SfmoltenPost::ARTICLE_TYPE, :name => "The title", :body__c => "The bod")
  end
end
