/**
 * 
 */
package org.projectsin.client.impl;

import java.io.IOException;
import java.io.InputStream;
import java.util.Set;

import org.projectsin.client.api.SinSearchResult;

/**
 * @author ruslan
 *
 */
public interface SinSearchResultParser
{
  public SinSearchResult parseResult(InputStream is, Set<String> fieldSet, Set<String> countSet)
    throws IOException;
}
