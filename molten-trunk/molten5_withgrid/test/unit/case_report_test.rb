require File.dirname(__FILE__) + '/../test_helper'

class CaseReportTest < Test::Unit::TestCase
  
  fixtures :sfaccount, :sfcontact, :case_report
  
  def setup
    @highgroove = sfaccount(:highgroove)
    @derek = sfcontact(:derek_haynes)
    @open = case_report(:open)
  end
  
  # def test_reports_saved_to_contacts
  #   assert @derek.saved_case_reports.any?
  #   assert_equal @open.contact, @derek
  # end
  
  def test_reports_shareable
    assert @open.shared?
  end
  
  def test_query_persisted_safely
    cr = CaseReport.new({
      :name => "Cases in Process",
      :contact_id => 2,
      :account_id => "abc", # highgroove
      :shared => 0
    })
    cr.query = {
      'status' => ['In Process'],
      'order' => 'ASC',
      'sort' => 'sfcase.created_date'
    }
    cr.save
    
    assert_equal "order=ASC&sort=sfcase.created_date", cr.query
  end
  
  def test_parses_funky_query_strings_correctly
    query = <<-"EOM"
      &&
      &a=b&
      &=&
      &controller=x&
      &sloop=&
      &action=favre&
      &foo[]=blah&
      &foo[]=bazz&
    EOM
    assert_equal({
      'a' => 'b',
      'sloop' => '',
      'foo' => ['blah', 'bazz']
    }, CaseReport.to_options(query.tr("\t",'').gsub("      ","")))
    
    assert_equal({}, CaseReport.to_options(""))
  end
  
  def test_produces_correct_query_strings
    {
      "" => {},
      "foo=bar" => {'foo' => 'bar'},
      "a[]=1&a[]=2" => {'a' => ['1', '2']},
      "a=b&z=z&bar=baz" => {'a' => 'b', 'z' => 'z', 'bar' => 'baz'}
    }.each do |(expected, source)|
      assert_equal(expected, CaseReport.to_query_string(source))
    end
  end
  
end
