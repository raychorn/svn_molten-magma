require File.dirname(__FILE__) + '/../test_helper'

class SfccommentTest < Test::Unit::TestCase
  fixtures :sfccomment,:sfcontact,:sfcase, :sfuser, :app_setting

  def setup
    @emails = ActionMailer::Base.deliveries
    @emails.clear
  end
  
  def test_create
    # no email should be sent - case contact and comment creator the same
    comment = Sfccomment.new(:support_case => sfcase(:widget_stuck), :created_by => Sfuser.find(sfcase(:widget_stuck).contact.id),
                             :comment_body => "This is the body", :sf_id => 3)
    assert comment.save
    # assert @emails.any? # why? shouldn't be sent...
    
    Sfccomment.delete_all
    
    # email should be sent - case contact and comment creator different
    comment = Sfccomment.new(:support_case => sfcase(:widget_stuck), :created_by => sfuser(:chip),
                             :comment_body => "This is the body", :sf_id => 4)
    assert comment.save
    
    # disabled for now...
    assert @emails.empty?
    
    # enable...
    Sfccomment.delete_all
    AppSetting.find_by_name('Send Comment Notifications').update_attribute('value',AppSetting::SEND_COMMENT_NOTIFICATIONS[:send_notification])
    comment = Sfccomment.new(:support_case => sfcase(:widget_stuck), :created_by => sfuser(:chip),
                             :comment_body => "This is the body", :sf_id => 4)
    assert comment.save
    assert @emails.any?
    
    
  end
  
end
