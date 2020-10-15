ENV["RAILS_ENV"] = "test"
require File.expand_path(File.dirname(__FILE__) + "/../config/environment")
require 'test_help'

class Test::Unit::TestCase
  # Transactional fixtures accelerate your tests by wrapping each test method
  # in a transaction that's rolled back on completion.  This ensures that the
  # test database remains unchanged so your fixtures don't have to be reloaded
  # between every test method.  Fewer database queries means faster tests.
  #
  # Read Mike Clark's excellent walkthrough at
  #   http://clarkware.com/cgi/blosxom/2005/10/24#Rails10FastTesting
  #
  # Every Active Record database supports transactions except MyISAM tables
  # in MySQL.  Turn off transactional fixtures in this case; however, if you
  # don't care one way or the other, switching from MyISAM to InnoDB tables
  # is recommended.
  self.use_transactional_fixtures = true

  # Instantiated fixtures are slow, but give you @david where otherwise you
  # would need people(:david).  If you don't want to migrate your existing
  # test cases which use the @david style and don't mind the speed hit (each
  # instantiated fixtures translates to a database query per test method),
  # then set this back to true.
  self.use_instantiated_fixtures  = false

  # Add more helper methods to be used by all tests here...
  def current_contact
    Sfcontact.find_by_sf_id(@response.cookies['contact_id'] || @request.cookies['contact_id'])
  end
  
  # Add more helper methods to be used by all tests here...
  # Tests to ensure that the attributes provided ARE NOT VALID for the object.
  def assert_invalid(object,*attributes)
    object.valid?
    attributes.each do |a|
      assert(object.errors.invalid?(a.to_s),
             "Attribute [ #{a.to_s} ] is NOT invalid")
    end
  end
  
  def authenticate_contact(contact = sfcontact(:derek))
    @request.cookies['contact_id'] = contact.id
    assert_equal current_contact, contact
  end
  
  def logout_contact
    @request.cookies['contact_id'] = nil
    assert_nil current_contact
  end
  
  # Tests to ensure that the attributes provided ARE VALID for the object.
  def assert_valid(object,*attributes)
    object.valid?
    attributes.each do |a|
      assert(!object.errors.invalid?(a.to_s),
             "Attribute [ #{a.to_s} ] is invalid [ #{object.errors.on(a.to_s)} ]")
    end
  end
  
  def assert_email_sent
    assert ActionMailer::Base.deliveries.any?
    ActionMailer::Base.deliveries.clear
  end
  
  def assert_email_not_sent
    assert ActionMailer::Base.deliveries.empty?
  end
end
