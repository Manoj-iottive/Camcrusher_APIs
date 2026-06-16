package com.camcrusher.openlr;

import java.util.List;

public class DecodeResponse {
    private boolean matched;
    private List<Long> wayIds;
    private double positiveOffset;
    private double negativeOffset;
    private int direction;
    private String geometry;
    private double confidence;
    private String reason;

    // Getters and setters
    public boolean isMatched() { return matched; }
    public void setMatched(boolean matched) { this.matched = matched; }
    public List<Long> getWayIds() { return wayIds; }
    public void setWayIds(List<Long> wayIds) { this.wayIds = wayIds; }
    public double getPositiveOffset() { return positiveOffset; }
    public void setPositiveOffset(double positiveOffset) { this.positiveOffset = positiveOffset; }
    public double getNegativeOffset() { return negativeOffset; }
    public void setNegativeOffset(double negativeOffset) { this.negativeOffset = negativeOffset; }
    public int getDirection() { return direction; }
    public void setDirection(int direction) { this.direction = direction; }
    public String getGeometry() { return geometry; }
    public void setGeometry(String geometry) { this.geometry = geometry; }
    public double getConfidence() { return confidence; }
    public void setConfidence(double confidence) { this.confidence = confidence; }
    public String getReason() { return reason; }
    public void setReason(String reason) { this.reason = reason; }
}
