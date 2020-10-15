require File.dirname(__FILE__) + '/../test_helper'

class SfaccountTest < Test::Unit::TestCase
  fixtures :sfaccount, :sfcontact

  def setup
    @highgroove = sfaccount(:highgroove)
  end

  def test_contacts
    assert @highgroove.contacts.any?
  end
  
  def test_associated_contacts
    Sfaccount.find(:all).each do |a|
      assert_nothing_raised { a.associated_contacts }
    end
  end
end
