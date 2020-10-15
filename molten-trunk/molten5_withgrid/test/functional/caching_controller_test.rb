require File.dirname(__FILE__) + '/../test_helper'
require 'caching_controller'

# Re-raise errors caught by the controller.
class CachingController; def rescue_action(e) raise e end; end

class CachingControllerTest < Test::Unit::TestCase
  def setup
    @controller = CachingController.new
    @request    = ActionController::TestRequest.new
    @response   = ActionController::TestResponse.new
  end

  # Replace this with your real tests.
  def test_truth
    assert true
  end
end
