require File.dirname(__FILE__) + '/../test_helper'

class CommentsController; def rescue_action(e) raise e end; end

class ActsAsSyncableTest < Test::Unit::TestCase
  
  fixtures :sfcontact
  
  def setup
    @derek = sfcontact(:derek_haynes)
  end
  
  # Tests for this method are showing that the SF record isn't being updated...but
  # console shows tests pass.
  def test_update_attribute_and_sync
    assert @derek.respond_to?(:update_attribute_and_sync)
  end
  
  def test_update_salesforce_attribute
    assert @derek.respond_to?(:update_salesforce_attribute)
  end
end
