require File.dirname(__FILE__) + '/../test_helper'

class ContactAuthenticationTest < Test::Unit::TestCase
  fixtures :sfcontact, :sfcontact_setting, :sfssl
  
  def setup
    @sfderek = sfcontact(:derek_haynes)
    # @derek = Contact.find_by_email("derek.haynes@highgroove.com")
    Sfcontact.find(:all).each { |c| c.save }
    
    @emails = ActionMailer::Base.deliveries
    @emails.clear
  end
  
  def test_authentication
    # failure - email address doesn't exist
    email = "conanobrian@nbc.com"
    password = "im_great"
    assert_nil Sfcontact.authenticate(email,password)

    # failure - password doesn't match
    failed_logins_before = @sfderek.portal_login_fail_count__c || 0
    email = @sfderek.email
    password = "wrong_pass"
    assert_nil Sfcontact.authenticate(email,password)
    assert_not_nil @sfderek.reload.portal_last_login_fail_date__c
    # DISABLED BECAUSE OF SF ERRORS
    # assert_equal "1", @sfderek.portal_login_fail_count__c
    # reset data
    Sfcontact.update_all("portal_last_login_fail_date__c = NULL")
    Sfcontact.update_all("portal_login_fail_count__c = NULL")
    @sfderek.reload

    # failure - user not active
    failed_logins_before = @sfderek.portal_login_fail_count__c
    @sfderek.update_attribute("contact_status__c","Inactive")
    password = @sfderek.portal_password__c
    assert_nil Sfcontact.authenticate(email,password)
    assert_not_nil @sfderek.reload.portal_last_login_fail_date__c
    # DISABLED BECAUSE OF SF ERRORS
    # assert_equal "1", @sfderek.portal_login_fail_count__c
    
    # success
    @sfderek.update_attribute("contact_status__c","Active")
    assert_equal @sfderek, Sfcontact.authenticate(email,password)
    assert_not_nil @sfderek.reload.portal_last_login_date__c
    
    # failure - set portal privilige to nil
    @sfderek.update_attribute('portal_privilege__c',nil)
    assert_nil Sfcontact.authenticate(email,password)
  end
  
  def test_authenticate_by_token
    # failure - id doesnt't exist
    assert_nil Sfcontact.authenticate_by_token("asdff",@sfderek.token)
    
    # failure - token doesn't match
    assert_nil Sfcontact.authenticate_by_token(@sfderek.id,"blah")
    
    assert_not_nil @sfderek.reload.portal_last_login_fail_date__c
    # DISABLED BECAUSE OF SF ERRORS
    # assert_equal "1", @sfderek.portal_login_fail_count__c
    # reset data
    Sfcontact.update_all("portal_last_login_fail_date__c = NULL")
    Sfcontact.update_all("portal_login_fail_count__c = NULL")
    @sfderek.reload
     
    # failure - user not active
    failed_logins_before = @sfderek.portal_login_fail_count__c
    @sfderek.update_attribute("contact_status__c","Inactive")
    assert_nil Sfcontact.authenticate_by_token(@sfderek.id,@sfderek.token)
    assert_not_nil @sfderek.reload.portal_last_login_fail_date__c
    # DISABLED BECAUSE OF SF ERRORS
    # assert_equal "1", @sfderek.portal_login_fail_count__c
    
    # success
    @sfderek.update_attribute("contact_status__c","Active")
    assert_equal @sfderek, Sfcontact.authenticate_by_token(@sfderek.id,@sfderek.token)
    assert_not_nil @sfderek.reload.portal_last_login_date__c
    # DISABLED BECAUSE OF SF ERRORS
    # assert_equal "1", @sfderek.portal_login_count__c
  end
  
  def test_token
    # token already exists
    previous_token = @sfderek.token
    assert_not_nil previous_token
    
    # token doesn't exist...generate it
    @sfderek.settings.update_attribute('token',nil)
    next_token = @sfderek.token
    assert_not_nil next_token
    assert @sfderek.token != previous_token
    
    # make sure a new token isn't generated
    assert_equal next_token, @sfderek.token
  end
  
  def test_change_password
    Sfcontact.update_all("contact_status__c = 'Active'")
    
    # failure - password and password confirmation don't match
    password_before = @sfderek.portal_password__c
    @sfderek.change_password!('new_pass','dont_match')
    assert @sfderek.portal_password__c != password_before
    assert_invalid @sfderek, :portal_password__c
    
    # failure - password is too short
    @sfderek.change_password!('s','s')
    assert_invalid @sfderek, :portal_password__c
    
    # success
    @sfderek.change_password!('new_pass2','new_pass2')
    assert @sfderek.valid?
    assert_equal @sfderek, Sfcontact.authenticate(@sfderek.email,'new_pass2')
  end
  
  def test_forgot_password
    # failure - email does not exist
    assert_nil Sfcontact.forgot_password("billybob@nothing.com",nil)

    # success
    assert_equal @sfderek, Sfcontact.forgot_password(@sfderek.email,nil)
    assert @emails.any?
    assert @emails.first.body.grep(/http:\/\/localhost:3000\/contact\/change_password\//)
    
    # pass thru a host and port to use
    @emails.clear
    override_host = "www.test.com"
    override_port = "5000"
    Sfcontact.forgot_password(@sfderek.email,override_port,override_host)
    assert @emails.any?
    assert @emails.first.body.grep(/http:\/\/#{override_host}/)
  end
  
end