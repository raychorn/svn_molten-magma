require File.dirname(__FILE__) + '/../test_helper'

class SfcontactTest < Test::Unit::TestCase
  fixtures :sfcontact, :sfaccount, :sfcase, :sfsolution, :sfcontact_setting

  def setup
    Sfcontact.reset_last_confirm_date
    
    @derek = sfcontact(:derek)
    
    @emails = ActionMailer::Base.deliveries
    @emails.clear  
  end
  
  def test_reset_last_confirm_date
    Sfcontact.update_all('portal_last_confirm_date__c = NULL')
    Sfcontact.find(:all).each { |c| assert_nil c.portal_last_confirm_date__c }
    Sfcontact.reset_last_confirm_date
    Sfcontact.find(:all).each { |c| assert c.portal_last_confirm_date__c }
  end
  
  def test_company
    assert @derek.company.is_a?(Sfaccount)
  end
  
  def test_cases
    assert @derek.cases.first.is_a?(Sfcase)
  end
  
  def test_send_confirmations
    # don't send the confirmations - dates sent are less than the range
    Sfcontact.reset_last_confirm_date
    contacts = Sfcontact.send_confirmations
    assert contacts.empty?
    assert @emails.empty?
    
    # now send them
    Sfcontact.reset_last_confirm_date(12.years.ago)
    contacts = Sfcontact.send_confirmations
    assert contacts.any?
    assert @emails.any?    
    
    @emails.clear
    
    # try again...shouldn't send duplicates
    contacts = Sfcontact.send_confirmations
    assert contacts.empty?
    assert @emails.empty?
  end
  
  def test_privilege
    contact = Sfcontact.new
    
    # contact has no privilege set
    assert !contact.privilege?('Member')
    
    # contact is a Member
    contact.portal_privilege__c = 'Member'
    assert contact.privilege?('Member')
    
    # contact is not a Marketing Admin
    assert !contact.privilege?('Marketing Admin')
    
    # contact is a Support Admin, and thus a Member
    contact.portal_privilege__c = 'Support Admin'
    assert contact.privilege?('Member')
    
    # contact is a Support Admin, but not an Admin
    assert !contact.privilege?('Admin')
    
    # contact is an Admin, and thus a Member and a a Support Admin
    contact.portal_privilege__c = 'Admin'
    assert contact.privilege?('Member')
    assert contact.privilege?('Support Admin')
    assert contact.privilege?('Super User')
    
    # contact is an Admin
    assert contact.privilege?('Admin')
    
    # contact is a Super User
    contact.portal_privilege__c = 'Super User'
    assert contact.privilege?('Member')
    assert !contact.privilege?('Support Admin')
    assert !contact.privilege?('Admin')
  end
  
  def test_confirm
    sfcontact(:derek).update_attributes({:portal_last_confirm_date__c => 1.month.ago(AppConstants::CONFIRMATION_RANGE), 
                                         :portal_last_confirm_sent_date__c => 1.month.ago(AppConstants::CONFIRMATION_RANGE)} )
    
    # failure - no contact with provided id
    assert_nil Sfcontact.confirm('asdfdsfds',sfcontact(:derek).token)
    
    # failure - no contact with provided token
    assert_nil Sfcontact.confirm(sfcontact(:derek).id,'bad token')
    
    # success
    confirm_date_before = sfcontact(:derek).portal_last_confirm_date__c
    token_before = sfcontact(:derek).token
    assert_equal sfcontact(:derek), Sfcontact.confirm(sfcontact(:derek).id, sfcontact(:derek).token)
    
    assert Sfcontact.find(sfcontact(:derek).id).portal_last_confirm_date__c > confirm_date_before
    assert Sfcontact.find(sfcontact(:derek).id).token != token_before
  end
  
  def test_deactivate_unconfirmed
    # failure - no users beyond threshold
    Sfcontact.find(:first).update_attribute('portal_last_confirm_date__c', 1.month.since(AppConstants::CONFIRMATION_RANGE_LIMIT) )
    contacts = Sfcontact.deactivate_unconfirmed
    assert contacts.empty?
    
    # success
    Sfcontact.find(:first).update_attribute('portal_last_confirm_date__c', 1.month.ago(AppConstants::CONFIRMATION_RANGE_LIMIT) )
    contacts = Sfcontact.deactivate_unconfirmed
    assert_equal 1, contacts.size
    assert_equal Sfcontact.find(:first), contacts.first
    
    # try again...shouldn't find any
    assert Sfcontact.deactivate_unconfirmed.empty?
  end
  
  def test_file_download_access
    assert @derek.license_delivery_contact.nil?
    
    # no - value is nil
    assert !@derek.file_download_access?
    
    # no - value is No
    @derek.update_attribute('license_delivery_contact__c','No')
    assert !@derek.file_download_access?
    
    # yes - value is Yes
    @derek.update_attribute('license_delivery_contact__c','Yes')
    assert @derek.file_download_access?
  end
  
  def test_recently_updated_cases
    cases = @derek.recently_updated_cases
    assert cases.any?
    assert_equal cases, cases.sort { |x,y| y.last_modified_date <=> x.last_modified_date  }
  end
  
  def test_recent_viewings
    Sfcase.view(Sfcase.find(:first).id,@derek)
    # now the case's account list must include @derek's account
    # assert @derek.recent_sfcases.any?
    
    Sfsolution.view(Sfsolution.find(:first).id,@derek)
    # assert @derek.recent_sfsolutions.any?
  end
  
  def test_case_viewable
    @derek.save
    
    # no settings exist for status 'new', so viewable
    assert @derek.case_viewable?('new')
  end
  
  def test_toggle_case_viewable
    test_case_viewable
    
    @derek.toggle_case_viewable('new')
    assert !@derek.case_viewable?('new')
    
    @derek.toggle_case_viewable('new')
    assert @derek.case_viewable?('new')
  end
end
