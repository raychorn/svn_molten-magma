require 'rubygems'

class SfSchemaUpdater < ActiveRecord::Migration

  #@allaccounts=Account.find_all
  @acctColumns=Account.columns
  @sqlaccount=Sfaccount.columns
  
  @userColumns=User.columns
  @sqlUser=Sfuser.columns
  
  @sslColumns=SelfServiceUser.columns
  @sqlSsl=Sfssl.columns
  
  @caseColumns=Case.columns
  @sqlCase=Sfcase.columns
  
  @contColumns=Contact.columns
  @sqlContact=Sfcontact.columns
  
  @solColumns=Solution.columns
  @sqlSol=Sfsolution.columns
  
  @attachColumns=Attachment.columns
  @sqlAttach=Sfattach.columns
  
  @commentsColumns=CaseComment.columns
  @sqlComment=Sfccomment.columns
  
  @catdataColumns=CategoryData.columns
  @sqlCatdata=Sfcatdata.columns
  
  @catnodeColumns=CategoryNode.columns
  @sqlCatnode=Sfcatnode.columns
  
 
  
  def self.up
   
    @acctColumns.each do |acol|
        @colname=acol.name    
        @coltype=acol.type    
        colexist="False"
        @sqlaccount.each do |sfacctcol|
          sqlacol=sfacctcol.name                  
          if(sqlacol.to_s().downcase() == @colname.to_s().downcase())
            colexist="True"
          end
        end
        if (colexist.to_s()=="False")
          @datatype="string"
          if (@coltype.to_s().downcase()=="text"|| @coltype.to_s().downcase()=="string")              
            @datatype="string"                                                  
          elsif (@coltype.to_s().downcase()=="datetime")
            @datatype="datetime"
          elsif(@coltype.to_s().downcase()=="date")
            @datatype="date"   
          elsif(@coltype.to_s().downcase()=="integer")
            @datatype="int"
          elsif(@coltype.to_s().downcase()=="float")
            @datatype="float"                    
          else
            @datatype="string"   
          end 
          add_column "sfaccount", "#{@colname}",:"#{@datatype}"
        end
    end
    
    @userColumns.each do |acol|
        @colname=acol.name   
        @coltype=acol.type     
        colexist="False"
        @sqlUser.each do |sfacctcol|
          sqlacol=sfacctcol.name
          if(sqlacol.to_s().downcase() == @colname.to_s().downcase())
            colexist="True"
          end
        end
        if (colexist.to_s()=="False")
          @datatype="string"
          if (@coltype.to_s().downcase()=="text"|| @coltype.to_s().downcase()=="string")              
            @datatype="string"                                                  
          elsif (@coltype.to_s().downcase()=="datetime")
            @datatype="datetime"
          elsif(@coltype.to_s().downcase()=="date")
            @datatype="date"   
          elsif(@coltype.to_s().downcase()=="integer")
            @datatype="int"
          elsif(@coltype.to_s().downcase()=="float")
            @datatype="float"                    
          else
            @datatype="string"   
          end 
          add_column "sfuser", "#{@colname}",:"#{@datatype}"
        end
    end
    
    @sslColumns.each do |acol|
        @colname=acol.name
        @coltype=acol.type
        colexist="False"
        @sqlSsl.each do |sfacctcol|
          sqlacol=sfacctcol.name
          if(sqlacol.to_s().downcase() == @colname.to_s().downcase())
            colexist="True"
          end
        end
        if (colexist.to_s()=="False")
          @datatype="string"
          if (@coltype.to_s().downcase()=="text"|| @coltype.to_s().downcase()=="string")              
            @datatype="string"                                                  
          elsif (@coltype.to_s().downcase()=="datetime")
            @datatype="datetime"
          elsif(@coltype.to_s().downcase()=="date")
            @datatype="date"   
          elsif(@coltype.to_s().downcase()=="integer")
            @datatype="int"
          elsif(@coltype.to_s().downcase()=="float")
            @datatype="float"                    
          else
            @datatype="string"   
          end 
          add_column "sfssl", "#{@colname}",:"#{@datatype}"
        end
    end
    
    @caseColumns.each do |acol|
        @colname=acol.name
        @coltype=acol.type
        colexist="False"
        @sqlCase.each do |sfacctcol|
          sqlacol=sfacctcol.name
          if(sqlacol.to_s().downcase() == @colname.to_s().downcase())
            colexist="True"
          end
        end
        if (colexist.to_s()=="False")
          @datatype="string"
          if (@coltype.to_s().downcase()=="text"|| @coltype.to_s().downcase()=="string")              
            @datatype="string"                                                  
          elsif (@coltype.to_s().downcase()=="datetime")
            @datatype="datetime"
          elsif(@coltype.to_s().downcase()=="date")
            @datatype="date"   
          elsif(@coltype.to_s().downcase()=="integer")
            @datatype="int"
          elsif(@coltype.to_s().downcase()=="float")
            @datatype="float"                    
          else
            @datatype="string"   
          end 
          add_column "sfcase", "#{@colname}",:"#{@datatype}"
        end
    end
    
    @contColumns.each do |acol|
        @colname=acol.name
        @coltype=acol.type
        colexist="False"
        @sqlContact.each do |sfacctcol|
          sqlacol=sfacctcol.name
          if(sqlacol.to_s().downcase() == @colname.to_s().downcase())
            colexist="True"
          end
        end
        if (colexist.to_s()=="False")
          @datatype="string"
          if (@coltype.to_s().downcase()=="text"|| @coltype.to_s().downcase()=="string")              
            @datatype="string"                                                  
          elsif (@coltype.to_s().downcase()=="datetime")
            @datatype="datetime"
          elsif(@coltype.to_s().downcase()=="date")
            @datatype="date"   
          elsif(@coltype.to_s().downcase()=="integer")
            @datatype="int"
          elsif(@coltype.to_s().downcase()=="float")
            @datatype="float"                    
          else
            @datatype="string"   
          end 
          add_column "sfcontact", "#{@colname}",:"#{@datatype}"
        end
    end
    
    @solColumns.each do |acol|
        @colname=acol.name
        @coltype=acol.type
        colexist="False"
        @sqlSol.each do |sfacctcol|
          sqlacol=sfacctcol.name
          if(sqlacol.to_s().downcase() == @colname.to_s().downcase())
            colexist="True"
          end
        end
        if (colexist.to_s()=="False")
          @datatype="string"
          if (@coltype.to_s().downcase()=="text"|| @coltype.to_s().downcase()=="string")              
            @datatype="string"                                                  
          elsif (@coltype.to_s().downcase()=="datetime")
            @datatype="datetime"
          elsif(@coltype.to_s().downcase()=="date")
            @datatype="date"   
          elsif(@coltype.to_s().downcase()=="integer")
            @datatype="int"
          elsif(@coltype.to_s().downcase()=="float")
            @datatype="float"                    
          else
            @datatype="string"   
          end 
          add_column "sfsolution", "#{@colname}",:"#{@datatype}"
        end
    end
    
    @attachColumns.each do |acol|
        @colname=acol.name
        @coltype=acol.type
        colexist="False"
        @sqlAttach.each do |sfacctcol|
          sqlacol=sfacctcol.name
          if(sqlacol.to_s().downcase() == @colname.to_s().downcase())
            colexist="True"
          end
        end
        if (colexist.to_s()=="False")
          @datatype="string"
          if (@coltype.to_s().downcase()=="text"|| @coltype.to_s().downcase()=="string")              
            @datatype="string"                                                  
          elsif (@coltype.to_s().downcase()=="datetime")
            @datatype="datetime"
          elsif(@coltype.to_s().downcase()=="date")
            @datatype="date"   
          elsif(@coltype.to_s().downcase()=="integer")
            @datatype="int"
          elsif(@coltype.to_s().downcase()=="float")
            @datatype="float"                    
          else
            @datatype="string"   
          end 
          add_column "sfattach", "#{@colname}",:"#{@datatype}"
        end
    end
    
    @commentsColumns.each do |acol|
        @colname=acol.name
        @coltype=acol.type
        colexist="False"
        @sqlComment.each do |sfacctcol|
          sqlacol=sfacctcol.name
          if(sqlacol.to_s().downcase() == @colname.to_s().downcase())
            colexist="True"
          end
        end
        if (colexist.to_s()=="False")
          @datatype="string"
          if (@coltype.to_s().downcase()=="text"|| @coltype.to_s().downcase()=="string")              
            @datatype="string"                                                  
          elsif (@coltype.to_s().downcase()=="datetime")
            @datatype="datetime"
          elsif(@coltype.to_s().downcase()=="date")
            @datatype="date"   
          elsif(@coltype.to_s().downcase()=="integer")
            @datatype="int"
          elsif(@coltype.to_s().downcase()=="float")
            @datatype="float"                    
          else
            @datatype="string"   
          end 
          add_column "sfccomment", "#{@colname}",:"#{@datatype}"
        end
    end
    
    @catdataColumns.each do |acol|
        @colname=acol.name
        @coltype=acol.type
        colexist="False"
        @sqlCatdata.each do |sfacctcol|
          sqlacol=sfacctcol.name
          if(sqlacol.to_s().downcase() == @colname.to_s().downcase())
            colexist="True"
          end
        end
        if (colexist.to_s()=="False")
          @datatype="string"
          if (@coltype.to_s().downcase()=="text"|| @coltype.to_s().downcase()=="string")              
            @datatype="string"                                                  
          elsif (@coltype.to_s().downcase()=="datetime")
            @datatype="datetime"
          elsif(@coltype.to_s().downcase()=="date")
            @datatype="date"   
          elsif(@coltype.to_s().downcase()=="integer")
            @datatype="int"
          elsif(@coltype.to_s().downcase()=="float")
            @datatype="float"                    
          else
            @datatype="string"   
          end    
          add_column "sfcatdata", "#{@colname}",:"#{@datatype}"
        end
    end
    
    @catnodeColumns.each do |acol|
        @colname=acol.name
        @coltype=acol.type
        colexist="False"
        @sqlCatnode.each do |sfacctcol|
          sqlacol=sfacctcol.name
          if(sqlacol.to_s().downcase() == @colname.to_s().downcase())
            colexist="True"
          end
        end
        if (colexist.to_s()=="False")
          @datatype="string"
          if (@coltype.to_s().downcase()=="text"|| @coltype.to_s().downcase()=="string")              
            @datatype="string"                                                  
          elsif (@coltype.to_s().downcase()=="datetime")
            @datatype="datetime"
          elsif(@coltype.to_s().downcase()=="date")
            @datatype="date"   
          elsif(@coltype.to_s().downcase()=="integer")
            @datatype="int"
          elsif(@coltype.to_s().downcase()=="float")
            @datatype="float"                    
          else
            @datatype="string"   
          end    
          add_column "sfcatnode", "#{@colname}",:"#{@datatype}"
        end
    end    
       
  end
    


  def self.down
  end
end
