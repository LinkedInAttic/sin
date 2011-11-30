/**
 * 
 */
package org.projectsin.client.api;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * @author ruslan
 *
 */
public class SinSearchHit
{
  private long      _id;
  private long      _docid;
  private String    _srcData;
  private double    _score;
  private int       _grouphitscount;

  private Map<String,List<String>>  _fieldValues = new HashMap<String,List<String>>();
  
  public long getId()
  {
    return _id;
  }

  public void setId(long id)
  {
    _id = id;
  }

  public long getDocid()
  {
    return _docid;
  }

  public void setDocid(long docid)
  {
    _docid = docid;
  }

  public String getSrcData()
  {
    return _srcData;
  }

  public void setSrcData(String srcData)
  {
    _srcData = srcData;
  }

  public double getScore()
  {
    return _score;
  }

  public void setScore(double score)
  {
    _score = score;
  }

  public int getGrouphitscount()
  {
    return _grouphitscount;
  }

  public void setGrouphitscount(int grouphitscount)
  {
    _grouphitscount = grouphitscount;
  }

  public Map<String, List<String>> getFieldValues()
  {
    return _fieldValues;
  }

  public void addFieldValue(String field, String value)
  {
    List<String> values = _fieldValues.get(field);
    if(values == null)
    {
      values = new ArrayList<String>();
      _fieldValues.put(field, values);
    }
    values.add(value);
  }
}
