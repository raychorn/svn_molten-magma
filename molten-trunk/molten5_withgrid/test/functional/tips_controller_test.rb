require File.dirname(__FILE__) + '/../test_helper'
require 'tips_controller'

# Re-raise errors caught by the controller.
class TipsController; def rescue_action(e) raise e end; end

class TipsControllerTest < Test::Unit::TestCase
  
  def test_truth
    assert true
  end
end
