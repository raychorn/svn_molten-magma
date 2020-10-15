require File.dirname(__FILE__) + '/../test_helper'

class SolutionRelevancyTest < Test::Unit::TestCase
  fixtures :solution_relevancy

  def test_view_value
    assert_equal SolutionRelevancy.find(:first).view_value, SolutionRelevancy.view_value
  end
end
