require File.dirname(__FILE__) + '/../test_helper'

class SfcaseTest < Test::Unit::TestCase
  fixtures :sfcase, :sfcontact, :sfuser, :sfccomment

  def setup
    @case = sfcase(:widget_stuck)
    @derek = sfcontact(:derek)
  end
  
  def test_view
    Sfcase.view(@case.id,@derek)
    assert_equal @case, Sfcase.view(@case.id,@derek)
    assert @case.viewings(true).any?
    assert @derek.viewings(true).any?
  end
  
  def test_view_with_short_id
    sfcase = sfcase(:long_id)
    id = sfcase.sf_id[0..-4]
    assert_equal sfcase, Sfcase.view(id,@derek)
    assert_equal sfcase, Sfcase.view(sfcase.id,@derek)
  end
  
  def test_validations
    sfcase = Sfcase.new
    # don't validate by default
    assert_valid sfcase, :subject
    
    # validate - should get an error
    sfcase.validate_case_attributes = true
    assert_invalid sfcase, :subject
    
    # success
    sfcase.subject = "hey"
    assert_valid sfcase, :subject

  end
  
  ### assocations ###
  
  def test_contact
    assert @case.contact.is_a?(Sfcontact)
  end
  
  def test_last_modified_by
    assert_equal sfuser(:chip), @case.last_modified_by
  end
  
  def test_comments
    comment = sfccomment(:widstuck_comment)
    assert_nil comment.is_published
    assert_equal @case, comment.support_case
    
    # no published comments
    assert @case.comments.empty?
     
    # publish a comment
    assert comment.update_attribute('is_published', '1')
    assert @case.comments(true).any?
  end
  
  ### end association test ###
  
  def test_method_missing
    assert_equal @case.product__c, @case.product
  end
end
