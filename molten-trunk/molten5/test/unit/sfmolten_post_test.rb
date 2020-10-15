require File.dirname(__FILE__) + '/../test_helper'

class SfmoltenPostTest < Test::Unit::TestCase
  fixtures :sfmolten_post

  def test_find_articles
    do_create_article
    do_create_article
    assert SfmoltenPost.find_articles.any?
  end
  
  def test_tips_for_page
    do_create_tip
    do_create_tip('cases/show')
    assert_equal 2, SfmoltenPost.tips_for_page('cases','show').size
    assert_equal 1, SfmoltenPost.tips_for_page('solutions','show').size
  end
  
  def test_check_downtime_interval
    SfmoltenPost.destroy_all
    # no dt intervals exist
    assert_nil SfmoltenPost.check_downtime_interval
    
    # a dt interval exists, but not in the current time
    interval = SfmoltenPost.new(:valid_from__c => format_time(5.days.since), 
                                :valid_to__c => format_time(10.days.since),
                                :record_type_id => '01230000000DSOaAAO' )
    assert interval.save
    # assert_nil SfmoltenPost.check_downtime_interval
    
    # a dt invertal exists in the current time
    assert SfmoltenPost.update_all("valid_from__c = '#{format_time(2.days.ago)}'")
    assert SfmoltenPost.check_downtime_interval.is_a?(SfmoltenPost)
  end
  
  def test_title
    a = SfmoltenPost.new
    
    # has neither a name or a title_long
    assert_nil a.title
    
    # has a title_long field
    a.title_long__c = 'blah'
    assert_equal a.title_long__c, a.title
    
    # doesn't but has name
    a.title_long__c = ''
    a.name = 'hey'
    assert_equal a.name, a.title
  end
  
  private
  
  def format_time(time)
    time.strftime("%Y-%m-%d %H:%M:%S")
  end
  
  def do_create_article
    SfmoltenPost.create!(:record_type_id => SfmoltenPost::ARTICLE_TYPE, :name => "The title", :body__c => "The bod")
  end
  
  def do_create_tip(page = 'application')
    SfmoltenPost.create!(:record_type_id => SfmoltenPost::TIP_TYPE, :name => "The tip name", :body__c => "The bod",
                       :page__c => page)
  end
end
