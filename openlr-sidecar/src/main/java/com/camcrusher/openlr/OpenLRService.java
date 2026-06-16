package com.camcrusher.openlr;

import openlr.binary.ByteArray;
import openlr.binary.OpenLRBinaryDecoder;
import openlr.decoder.OpenLRDecoder;
import openlr.decoder.OpenLRDecoderParameter;
import openlr.location.Location;
import openlr.map.Line;
import openlr.rawLocRef.RawLocationReference;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import jakarta.annotation.PostConstruct;
import java.io.File;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;

@Service
public class OpenLRService {

    @Value("${osm.pbf.path}")
    private String pbfPath;

    private OsmMapDatabase mapDatabase;
    private OpenLRDecoder decoder;

    @PostConstruct
    public void init() {
        try {
            System.out.println("Loading OSM map from: " + pbfPath);
            mapDatabase = new OsmMapDatabase(new File(pbfPath));
            mapDatabase.load();
            decoder = new OpenLRDecoder();
            System.out.println("OSM map loaded successfully");
        } catch (Exception e) {
            System.err.println("Failed to load OSM map: " + e.getMessage());
        }
    }

    public DecodeResponse decode(String base64OpenLR) {
        DecodeResponse response = new DecodeResponse();
        try {
            byte[] bytes = Base64.getDecoder().decode(base64OpenLR);
            ByteArray byteArray = new ByteArray(bytes);

            OpenLRBinaryDecoder binaryDecoder = new OpenLRBinaryDecoder();
            RawLocationReference rawRef = binaryDecoder.decodeData("loc", byteArray);

            OpenLRDecoderParameter params = new OpenLRDecoderParameter.Builder()
                    .with(mapDatabase)
                    .buildParameter();

            Location location = decoder.decode(params, rawRef);

            if (location != null && location.isValid()) {
                List<Long> wayIds = new ArrayList<>();
                List<Line> lines = location.getLocationLines();
                if (lines != null) {
                    for (Line line : lines) {
                        wayIds.add(line.getID());
                    }
                }
                response.setMatched(true);
                response.setWayIds(wayIds);
                response.setPositiveOffset(
                    location.getPositiveOffset() != null ?
                    location.getPositiveOffset() / 100.0 : 0.0);
                response.setNegativeOffset(
                    location.getNegativeOffset() != null ?
                    location.getNegativeOffset() / 100.0 : 0.0);
                response.setDirection(0);
                response.setConfidence(0.9);
                response.setGeometry(buildWKT(lines));
            } else {
                response.setMatched(false);
                response.setReason("location invalid or null");
            }
        } catch (Exception e) {
            response.setMatched(false);
            response.setReason(e.getMessage());
        }
        return response;
    }

    private String buildWKT(List<Line> lines) {
        if (lines == null || lines.isEmpty()) return null;
        StringBuilder sb = new StringBuilder("LINESTRING(");
        boolean first = true;
        for (Line line : lines) {
            if (!first) sb.append(",");
            sb.append(line.getStartNode().getLongitudeDeg())
              .append(" ")
              .append(line.getStartNode().getLatitudeDeg());
            first = false;
        }
        Line last = lines.get(lines.size() - 1);
        sb.append(",")
          .append(last.getEndNode().getLongitudeDeg())
          .append(" ")
          .append(last.getEndNode().getLatitudeDeg());
        sb.append(")");
        return sb.toString();
    }
}
