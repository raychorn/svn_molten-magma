class ArticlesController < ProtectedController

  def sidebar
    @articles = SfmoltenPost.find_articles(:limit => AppConstants::ARTICLE_LIMIT)
    render(:layout => false)
  end
  
  def list
    @articles = SfmoltenPost.find_articles(:limit => AppConstants::ARTICLE_LIMIT)
    render(:action => 'list')
  end
  alias index list
  
  def show
    @article = SfmoltenPost.find_article(params[:id])
  end
end
